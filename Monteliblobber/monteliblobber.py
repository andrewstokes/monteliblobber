""" Monteliblobber: A reasonable way to extract and contextualize network artifacts from blobs.
"""

from flask import Flask, render_template, request, jsonify, json, abort
import ipaddress
import re
import geoip2.database
import requests
import gzip
import os
import sys
import string
import webbrowser


def setup_application():
    if getattr(sys, 'frozen', False):
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        application = Flask(__name__, instance_relative_config=True, template_folder=template_folder,
                            static_folder=static_folder)
    else:
        application = Flask(__name__, instance_relative_config=True)

    # Import configuration
    try:
        application.config.from_object('Monteliblobber.settings.Config')
    except ImportError:
        application.config.from_object('settings.Config')

    # Create config directory root.
    if not os.path.isdir(application.config['LOCAL_CONF_DIR']):
        os.mkdir(application.config['LOCAL_CONF_DIR'])

    # Import local config if it exists.
    if os.path.isfile(application.config['LOCAL_CONF_FILE']):
        application.config.from_pyfile(application.config['LOCAL_CONF_FILE'])

    # Converts the `NAMED_NETWORK` String IP and network values to `ipaddress` objects when the app initializes.
    for name, networks in application.config['NAMED_NETWORKS'].items():
        net_objects = []
        for net in networks:
            net_objects.append(ipaddress.ip_network(net))
        application.config['NAMED_NETWORKS'][name] = net_objects

    # Converts the white listed IP and network Strings to `ipaddress` objects when the app initializes.
    converted = []
    for address in application.config['WHITELISTS']['network_addresses']:
        converted.append(ipaddress.ip_network(address))
    application.config['WHITELISTS']['network_addresses'] = converted

    return application


app = setup_application()


@app.route('/', methods=['POST', 'GET'])
def index():
    """ The primary route for the root path.

    :return: HTTP Template or JSON Response Objects
    """

    if request.method == 'POST':
        results = extract_indicators(request.form['blob'])
        return jsonify({'data': results})
    else:
        ctx = {}
        if not preflight_check(
                app.config['BLACKLIST_DB'],
                app.config['MAXMIND_CITY_DB_PATH'],
                app.config['ROOT_DOMAINS_PATH']
        ):
            ctx.update(
                {'errors': [
                    'One of the lookup files is not present. '
                    'Run the updaters from the Actions menu! '
                    'This message will disappear when all files are present.'
                ]}
            )
        return render_template('index.html', **{'context': ctx})


@app.route('/file', methods=['POST', 'GET'])
def submit_file():
    """ Allows for submission of file objects for sifting.

    :return: HTTP Template or JSON Response Objects
    """

    if request.method == 'POST':
        if 'file' in request.files:
            filename = os.path.join(app.config['LOCAL_CONF_DIR'], '.temp_upload.dat')
            file = request.files['file']
            file.save(filename)
            del file
            with open(filename, errors='ignore') as f:
                data = extract_strings(f)
                app.config['RESULTS'] = extract_indicators(data)
            os.remove(filename)

            return render_template('file_submission.html')
        else:
            ctx = {'errors': [
                'No file was submitted. Please try again! '
            ]}
            return render_template('index.html', **{'context': ctx})
    else:
        abort(404)


@app.route('/results', methods=['GET'])
def get_results():
    """ Returns the results from a file based submission.

    :return: JSON Response Object
    """

    results = app.config['RESULTS'].copy()
    del app.config['RESULTS']  # Remove stored results
    return jsonify({'data': results})


@app.route('/update_roots', methods=['POST'])
def update_root_domains():
    """ Updates the root domain list.

    :return: JSON Response Object
    """

    get_root_domains(app.config['ROOT_DOMAINS_URL'], app.config['ROOT_DOMAINS_PATH'])

    return jsonify({'status': 200})


@app.route('/update_geoip', methods=['POST'])
def update_geoip():
    """ Updates the GEO IP database.

    :return: JSON Response Object
    """

    get_geoip_database(app.config['GEOIP_DB_URL'], app.config['MAXMIND_CITY_DB_PATH'])

    return jsonify({'status': 200})


@app.route('/update_blacklists', methods=['POST'])
def update_blacklists():
    """ Updates the file containing blacklisted IPs.

    :return: JSON Response Object
    """

    get_blacklists(app.config['BLACKLISTS'], app.config['BLACKLIST_DB'])
    return jsonify({'status': 200})


@app.route('/update_all', methods=['POST'])
def update_all():
    """ Updates all static files.

    :return: JSON Response Object
    """

    get_root_domains(app.config['ROOT_DOMAINS_URL'], app.config['ROOT_DOMAINS_PATH'])
    get_geoip_database(app.config['GEOIP_DB_URL'], app.config['MAXMIND_CITY_DB_PATH'])
    get_blacklists(app.config['BLACKLISTS'], app.config['BLACKLIST_DB'])
    return jsonify({'status': 200})


@app.route('/<path:path>', methods=['GET'])
def static_proxy(path):
    """ Route that serves static files.

    :param path: URI String
    :return: Response Object containing a static file
    """

    return app.send_static_file(path)


def preflight_check(blacklist_file, geoip_file, root_domains_file):
    """ Checks the existence of all the lookup files. Returns False if one is missing.

    :return: Bool
    """

    if not os.path.isfile(blacklist_file):
        return False
    elif not os.path.isfile(geoip_file):
        return False
    elif not os.path.isfile(root_domains_file):
        return False
    else:
        return True


def extract_indicators(text_blob):
    """ The primary function that handles combining all the functions involved with extracting
    and analyzing artifacts from the incoming text blobs.

    :param text_blob: String
    :return: A list of dictionaries containing artifacts.
    """

    artifacts = []
    artifacts.extend(
        get_network_addresses(
            text_blob,
            app.config['MAXMIND_CITY_DB_PATH'],
            app.config['BLACKLIST_DB'],
            app.config['NAMED_NETWORKS'],
            app.config['WHITELISTS']['network_addresses']
        )
    )
    artifacts.extend(get_email_addresses(text_blob, app.config['WHITELISTS']['domains']))
    artifacts.extend(get_urls(text_blob, app.config['WHITELISTS']['domains']))
    artifacts.extend(
        get_hostnames(
            text_blob,
            app.config['ROOT_DOMAINS_PATH'],
            app.config['WHITELISTS']['domains']
        )
    )
    return artifacts


def get_root_domains(url, filename):
    """ Updates root domain file.

    :param url: URL of the root domains list.
    :param filename: File name to write the list.
    """

    r = requests.get(url)
    with open(filename, 'w') as f:
        f.write(r.text)
    return True


def get_blacklists(blacklist_config, filename):
    """ Updates blacklist file.

    :param blacklist_config: A dict object containing Name/Url key value pairs.
    :param filename: File name to write the lists.
    """

    blacklists = get_blacklist_items(blacklist_config)
    with open(filename, 'w') as f:
        json.dump(blacklists, f)
    return True


def get_geoip_database(url, filename):
    """ Updates root domain file.

    :param url: URL of the MaxMind GeoIP City Database.
    :param filename: File name to write the db.
    """

    r = requests.get(url)
    with open(filename, 'wb') as f:
        data = gzip.decompress(r.content)
        f.write(data)
    return True


def extract_strings(stream):
    """ Returns a string containing strings extracted from a file. Used to process binary input.

    :param stream: A file stream
    :return: String
    """

    chars = string.printable
    min_length = 4
    results = ""
    result = ""
    for c in stream.read():
        if c in chars:
            result += c
            continue
        if len(result) >= min_length:
            results += result + " "
        result = ""
    if len(result) >= min_length:
        results += result + " "
    return results


def get_network_addresses(text_blob, geoip_file, blacklist_file, named_networks, whitelisted_addresses):
    """ Extracts network addresses from text.

    :param text_blob: String
    :param geoip_file: Path to the geoip database file.
    :param blacklist_file: Path to the blacklist JSON file.
    :param named_networks: Dictionary object containing name, `ipaddress.ip_network` pairs.
    :param whitelisted_addresses: List of `ipaddress.IPNetwork` objects used to filter matches from the results.
    :return: A list of dictionaries containing network addresses.
    """

    network_addresses = []
    ip_regex = re.compile(
        r'''(?P<ip_address>(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9]))'''
    )
    ip_matches = ip_regex.findall(text_blob)
    if ip_matches:
        for i in dedup_list(ip_matches):
            # Filter white listed addresses.
            if not whitelist_lookup(i, whitelisted_addresses):
                network_addresses.append({'value': i, 'data_type': 'ipv4_address'})
        network_addresses = analyze_network_address(
            network_addresses,
            geoip_file,
            blacklist_file,
            named_networks
        )
    return network_addresses


def get_email_addresses(text_blob, whitelist):
    """ Returns a list of dict objects containing de-duplicated email addresses filtered through a white list.

    :param text_blob: String
    :param whitelist: A list of strings containing white listed domains.
    :return: A list if dictionaries containing email addresses.
    """
    email_addresses = []
    email_regex = re.compile(
        r'''(?P<email>[a-zA-Z0-9\.]+@[a-zA-Z0-9]+(?:\-)?[a-zA-Z0-9]+(?:\.)?[a-zA-Z0-9]{2,6}?\.[a-zA-Z]{2,6})'''
    )
    email_matches = email_regex.findall(text_blob)
    if email_matches:
        for i in dedup_list(email_matches):
            if not check_domain_whitelist(i, whitelist):
                email_addresses.append({'value': i, 'data_type': 'email', 'tags': []})
    return email_addresses


def get_urls(text_blob, whitelist):
    """ Returns a list of dict objects containing de-duplicated urls filtered through a white list.

    :param text_blob: String
    :param whitelist: A list of strings containing white listed domains.
    :return: A list of dictionaries containing URLs.
    """

    urls = []
    url_regex = re.compile(
        r'''(?P<url>\b(?:https?|ftp|file):\/\/[\-A-Za-z0-9+&@#\/%?=~_|!:,.;]*[\-A-Za-z0-9+&@#\/%=~_])'''
    )
    url_matches = url_regex.findall(text_blob)
    if url_matches:
        for i in dedup_list(url_matches):
            if not check_domain_whitelist(i, whitelist):
                urls.append({'value': i, 'data_type': 'url', 'tags': []})
    return urls


def get_hostnames(text_blob, root_domains, whitelist):
    """ Extracts host names from text.

    :param text_blob: String
    :param root_domains: Path to the root domains file.
    :param whitelist: A list of strings containing white listed domains.
    :return: A list of dictionaries containing host names.
    """

    hostnames = []
    hostname_regex = re.compile(
        r'''(?P<hostname>(?:[a-z0-9_\-]{1,5})?(?:(?:[a-z0-9_\-]{1,})(?::(?:[a-z0-9_\-]{1,}))?)?(?:(?:www\.)|(?:[a-z0-9_\-]{1,}\.)+)?(?:[a-z0-9_\-]{3,})\.(?:[a-z]{2,4})(?:\/(?:[a-z0-9_\-]{1,}\/)+)?(?:[a-z0-9_\-]{1,})?(?:\.[a-z]{2,})?(?:\?)?(?:(?:(?:\&)?[a-z0-9_\-]{1,}(?:\=[a-z0-9_\-]{1,})?)+)?)'''
    )
    hostname_matches = hostname_regex.findall(text_blob)
    if hostname_matches:
        deduped = dedup_list(hostname_matches)
        valid = validate_root_domain(deduped, root_domains)
        for i in valid:
            if not check_domain_whitelist(i, whitelist):
                hostnames.append({'value': i, 'data_type': 'dns_name', 'tags': []})
    return hostnames


def check_domain_whitelist(string, whitelist):
    """ Returns True if a white listed domain appears in the string, otherwise returns False.

    :param string: A string possibly containing a domain name.
    :param whitelist: A list of strings containing white listed domains.
    :return: Bool
    """

    for i in whitelist:
        if i in string:
            return True
    return False


def analyze_network_address(ips, geoip_file, blacklist_file, named_networks):
    """ Performs geoip, blacklist, and named network lookups on network addresses. The country name is added to a
     list object and then added to the original dictionary under the `tags` key.

    The expected data structure is a list of dictionary objects with `type` and `value` keys defined.

    Input Example:

    ```
    [
      {
        "type": "ip_address",
        "value": "8.8.8.8"
      },
    ]
    ```

    :param ips: A list of dictionary objects
    :param geoip_file: Path to the geoip database file.
    :param blacklist_file: Path to the blacklist JSON file.
    :param named_networks: Dictionary object containing name, `ipaddress.ip_network` pairs.
    :return:
    """

    # Setup the GeoIP Reader
    reader = geoip2.database.Reader(geoip_file)

    # Setup the blacklist DB in memory.
    with open(blacklist_file, 'r') as f:
        blacklist = json.load(f)
    for item in blacklist:
        if item['type'] == 'ip_address':
            item['value'] = ipaddress.ip_address(item['value'])
        else:
            item['value'] = ipaddress.ip_network(item['value'])
    blacklist_memory_db = blacklist
    del blacklist

    # Begin analyzing extracted IP addresses.
    for i in ips:
        ip = ipaddress.ip_address(i['value'])
        tags = []
        try:
            result = reader.city(i['value'])
            tags.append(result.registered_country.name)
            if result.traits.is_anonymous_proxy:
                tags.append('Anon Proxy')
            named = named_network_lookup(ip, named_networks)
            if named:
                tags.append(named)
            bl = blacklist_lookup(ip, blacklist_memory_db)
            if bl:
                tags.append(bl)
        except geoip2.errors.AddressNotFoundError:
            tag = None
            if ip.is_link_local:
                tag = 'Link Local'
            elif ip.is_loopback:
                tag = 'Loopback'
            elif ip.is_multicast:
                tag = 'Multicast'
            elif ip.is_private:
                tag = 'Private'
            elif ip.is_reserved:
                tag = 'Reserved'
            elif ip.is_unspecified:
                tag = 'Unspecified'
            tags.append(tag)
        i.update({'tags': tags})
    return ips


def named_network_lookup(ip_address, named_networks):
    """ Returns the name of the network or `None` if no matching IP was found in the `named_networks`.

    :param ip_address: String IPv4 Network Address
    :param named_networks: Dictionary object containing name, `ipaddress.ip_network` pairs.
    :return: String or None
    """

    for network_name, network_objects in named_networks.items():
        for n in network_objects:
            if ip_address in n:
                return network_name

    return None


def whitelist_lookup(ip_address, whitelisted_addresses):
    """ Returns True if `ip_address` is found in the `ipaddress.ip_networks` contained in `whitelisted_addresses`.
    Otherwise returns False.

    :param ip_address: String IPv4 Address
    :param whitelisted_addresses: List of `ipaddress.IPv4Network`
    :return: Bool
    """
    ip = ipaddress.ip_address(ip_address)
    for net in whitelisted_addresses:
        if ip in net:
            return True
    return False


def blacklist_lookup(ip_address, blacklist_mem_db):
    """ Queries the in memory DB of blacklisted addresses for an IPv4 address. Returns the blacklist name
     or `None` of no matching IP was found.

    :param blacklist_mem_db: Object containing the in memory blacklist db.
    :param ip_address: String IPv4 Network Address
    :return: String or None
    """

    for item in blacklist_mem_db:
        if item['type'] == 'ip_network' and ip_address in item['value']:
            return item['name']
        elif ip_address == item['value']:
            return item['name']


def dedup_list(items):
    """ Performs a de-duplication routine on a list of strings.

    :param items: List of Strings
    :return: De-duplicated List of Strings
    """

    deduped = []
    pos = 0
    items.sort()
    for i in items:
        if i != items[pos - 1]:
            deduped.append(i)
        pos += 1
    del items
    return deduped


def validate_root_domain(items, root_domains):
    """ Filters a list of potential FQDN's by cross checking the domain with IANA's list of valid root domains.

    :param items: List of FQDN strings
    :param root_domains: Path to the root domains file.
    :return: A filtered List of FQDN strings
    """

    valid = []
    with open(root_domains, 'r') as f:
        roots = [i.lower().strip('\n') for i in f]
        for hostname in items:
            root = hostname.split('.')[-1]
            if root in roots:
                valid.append(hostname)
        del roots
    del items
    return valid


def download_updated_root_domains():
    """ Downloads the current root domain file from IANA and saves it in the temp config
    directory as `root_domains.txt`.
    """

    r = requests.get(app.config['ROOT_DOMAINS_URL'])
    with open(app.config['ROOT_DOMAINS_LIST']) as f:
        f.write(r.content)


def convert_list_to_string(in_list):
    """ Concatenates a list of strings into a single string.

    :param in_list: List of Strings
    :return: String
    """

    out_string = ''
    for item in in_list:
        out_string += item + ', '
    return out_string[:-2]


def request_blacklist(url, bl_name):
    """ Downloads a blacklist file and uses IP or CIDR addresses defined in `settings.IP_FILTER` to
     remove networks or IPs from the blacklist.

    :param url: The blacklist file URL
    :param bl_name: Name of the blacklist
    :return: List of Dictionary Objects
    """

    filtered_ip_list = []
    data_type = 'ip_address'
    if '.netset' in url:
        data_type = 'ip_network'
    r = requests.get(url)
    p = re.compile(r'^\d.+', re.MULTILINE)
    for match in re.findall(p, r.text):
        ip = match.strip('\n')
        if not re.match(re.compile(app.config['IP_FILTER']), ip):
            data = {'name': bl_name, 'type': data_type, 'value': ip}
            filtered_ip_list.append(data)
    return filtered_ip_list


def get_blacklist_items(url_dict):
    """ Aggregates IPs and networks from multiple blacklists.

    :param url_dict: Dictionary containing `URL` and `name` KV pairs.
    :return: List of Dictionary Objects
    """

    blacklist_items = []
    for name, url in url_dict.items():
        blacklist = request_blacklist(url, name)
        blacklist_items.extend(blacklist)
    return blacklist_items


if __name__ == '__main__':

    if app.config['AUTO_OPEN_BROWSER']:
        webbrowser.open_new_tab('http://' + app.config['SERVER_NAME'])

    app.run(host=app.config['HOST'], port=app.config['PORT'])
