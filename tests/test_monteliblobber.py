
import unittest
import ipaddress
from flask import json
from Monteliblobber import monteliblobber
from Monteliblobber.settings import Config
import os


# Create config object.
c = Config()

TEST_ROOT = os.path.dirname(os.path.abspath(__file__))

# Acquire test blob data
with open(os.path.join(TEST_ROOT, 'email_message_source.txt'), 'r') as f:
    TEST_BLOB = f.read()


class MonteliblobberTestCase(unittest.TestCase):

    def setUp(self):

        self.config = Config()

        self.preflight = monteliblobber.preflight_check
        monteliblobber.app.config['TESTING'] = True
        # Add additional white list entries
        self.config.WHITELISTS['domains'].extend(['apple.com', 'email.com'])

        # Add additional named networks
        self.config.NAMED_NETWORKS.update({'WATCH': [ipaddress.ip_network('87.236.220.0/24')]})

        self.ips = ['72.167.218.149', '87.236.220.167']
        self.tags = ['United States', 'Spain', 'WATCH']
        self.urls = ['http://yvonneevans.net/wp-content/plugins/the-events-calendar/resources/tumour.php']
        self.hostnames = [
            '87-236-220-167.factoriadigital.com',
            'jantje.com',
            'p3plibsmtp03-02.prod.phx3.secureserver.net',
            'p3plsmtp03-01.prod.phx3.secureserver.net'
        ]
        self.addresses = ['jantje@jantje.com']
        self.app = monteliblobber.app.test_client()

    def tearDown(self):
        pass

    def test_extract_ip_addresses(self):
        """ IP Address are extracted and tagged correctly.
        """
        data = monteliblobber.get_network_addresses(
            TEST_BLOB,
            self.config.MAXMIND_CITY_DB_PATH,
            self.config.BLACKLIST_DB,
            self.config.NAMED_NETWORKS,
            self.config.WHITELISTS['network_addresses']
        )

        for record in data:
            with self.subTest(record['value']):
                self.assertIn(record['value'], self.ips)
            with self.subTest(record['tags']):
                for tag in record['tags']:
                    self.assertIn(tag, self.tags)

    def test_extract_urls(self):
        """ One URL is extracted. URLs with a white listed domain are not present.
        """
        data = monteliblobber.get_urls(TEST_BLOB, self.config.WHITELISTS['domains'])

        for record in data:
            with self.subTest(record['value']):
                self.assertIn(record['value'], self.urls)

    def test_extract_hostnames(self):
        """ Hostnames are extracted, except those with a white listed domain.
        """
        data = monteliblobber.get_hostnames(
            TEST_BLOB,
            self.config.ROOT_DOMAINS_PATH,
            self.config.WHITELISTS['domains']
        )

        for record in data:
            with self.subTest(record['value']):
                self.assertIn(record['value'], self.hostnames)

    def test_extract_email_addresses(self):
        """ Email addresses are extracted, except those with a white listed domain.
        """
        data = monteliblobber.get_email_addresses(TEST_BLOB, self.config.WHITELISTS['domains'])

        for record in data:
            with self.subTest(record['value']):
                self.assertIn(record['value'], self.addresses)

    def test_integration(self):
        """ All artifacts are extracted through the web service.
        """
        rv = self.app.post('/', data={'blob': TEST_BLOB})
        data = json.loads(rv.data)['data']
        for record in data:
            with self.subTest(record['value']):
                if record['data_type'] == 'ipv4_address':
                    self.assertIn(record['value'], self.ips)
            with self.subTest(record['value']):
                if record['data_type'] == 'url':
                    self.assertIn(record['value'], self.urls)
            with self.subTest(record['value']):
                if record['data_type'] == 'dns_name':
                    self.assertIn(record['value'], self.hostnames)
            with self.subTest(record['value']):
                if record['data_type'] == 'email':
                    self.assertIn(record['value'], self.addresses)
            with self.subTest(record['tags']):
                if len(str(record['tags'])) > 0:
                    for tag in record['tags']:
                        self.assertIn(tag, self.tags)

    def test_lookup_files_exist(self):
        result = self.preflight(
            self.config.BLACKLIST_DB,
            self.config.MAXMIND_CITY_DB_PATH,
            self.config.ROOT_DOMAINS_PATH
        )
        assert result


def setUpModule():
    # If local config directory exists, ensure empty, else create the directory.
    if os.path.isdir(c.LOCAL_CONF_DIR):
        files = os.listdir(c.LOCAL_CONF_DIR)
        for file in files:
            os.remove(os.path.join(c.LOCAL_CONF_DIR, file))
    else:
        os.mkdir(c.LOCAL_CONF_DIR)

    # Download fresh static files.
    monteliblobber.get_root_domains(c.ROOT_DOMAINS_URL, c.ROOT_DOMAINS_PATH)
    monteliblobber.get_geoip_database(c.GEOIP_DB_URL, c.MAXMIND_CITY_DB_PATH)
    monteliblobber.get_blacklists(c.BLACKLISTS, c.BLACKLIST_DB)


def tearDownModule():
    # Clean up the local config directory and files.
    files = os.listdir(c.LOCAL_CONF_DIR)
    for file in files:
        os.remove(os.path.join(c.LOCAL_CONF_DIR, file))
    os.removedirs(c.LOCAL_CONF_DIR)


if __name__ == '__main__':
    unittest.main()

