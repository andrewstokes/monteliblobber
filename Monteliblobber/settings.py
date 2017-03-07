

import os

# DEFAULT USER DEFINED SETTINGS

DEFAULT_LABELED_NETWORKS = {
    'GOOG': ['209.85.192.0/24', '74.125.82.0/24', '8.8.8.8'],
    'MSFT': ['131.107.0.0/16', '207.46.0.0/16']
}

DEFAULT_WHITELISTS = {
    'domains': ['google.com', 'microsoft.com', 'outlook.com'],
    'network_addresses': ['127.0.0.1', '10.0.0.0/8']
}

DEFAULT_BLACKLISTS = {
        'dshield_7D': 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/dshield_7d.netset',
        'bambenek_c2': 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/bambenek_c2.ipset',
        'alienvault': 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/alienvault_reputation.ipset',
        'tor_exit': 'https://raw.githubusercontent.com/firehol/blocklist-ipsets/master/tor_exits.ipset'
    }

DEFAULT_AUTO_OPEN_BROWSER = True


class Config(object):

    DEBUG = False
    TESTING = False
    APP_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    USER_HOME_DIRECTORY = os.path.expanduser('~')
    LOCAL_CONF_DIR = os.path.join(USER_HOME_DIRECTORY, '.monteliblobber')
    LOCAL_CONF_FILE = os.path.join(LOCAL_CONF_DIR, 'monteliblobber.cfg')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024
    MAXMIND_CITY_DB_PATH = os.path.join(LOCAL_CONF_DIR, 'GeoLite2-City.mmdb')
    NAMED_NETWORKS = DEFAULT_LABELED_NETWORKS
    WHITELISTS = DEFAULT_WHITELISTS
    AUTO_OPEN_BROWSER = DEFAULT_AUTO_OPEN_BROWSER
    IP_FILTER = r'^127.+|^0.+|^172\.\d\d.+|^224.+|^238.+|^10\..+|^169\.254.+|^192\.168.+'
    ROOT_DOMAINS_PATH = os.path.join(LOCAL_CONF_DIR, 'root_domains.txt')
    ROOT_DOMAINS_URL = 'http://data.iana.org/TLD/tlds-alpha-by-domain.txt'
    GEOIP_DB_URL = 'http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz'
    BLACKLIST_DB = os.path.join(LOCAL_CONF_DIR, 'blacklist_db.json')
    BLACKLIST_MEM_DB = None
    BLACKLISTS = DEFAULT_BLACKLISTS
    HOST = '127.0.0.1'
    PORT = 5007
    SERVER_NAME = HOST + ':' + str(PORT)
