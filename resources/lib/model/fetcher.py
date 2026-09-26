import os

import requests

# Prefer the OS CA bundle over script.module.certifi, whose cacert.pem is
# outdated in the Kodi repo and fails to verify www.ted.com.
SYSTEM_CA_BUNDLES = [
    '/etc/ssl/cert.pem',
    '/etc/ssl/certs/ca-certificates.crt',
    '/etc/pki/tls/certs/ca-bundle.crt',
    '/etc/ssl/ca-bundle.pem',
    '/usr/local/share/certs/ca-root-nss.crt',
]

TIMEOUT_SECONDS = 30


def _system_ca_bundle():
    for bundle in SYSTEM_CA_BUNDLES:
        if os.path.isfile(bundle):
            return bundle
    return None


class Fetcher:

    def __init__(self, logger):
        self.logger = logger
        self.session = requests.Session()
        bundle = _system_ca_bundle()
        if bundle:
            self.session.verify = bundle

    def get(self, url):
        self.logger('GET {}'.format(url))

        r = self.session.get(url, timeout=TIMEOUT_SECONDS)
        if r.ok:
            return r
        else:
            self.logger('%s\n%s\n%s' % (r.status_code, r.headers, r.text))
            raise Exception('Failed to GET {}: {}'.format(url, r.status_code))


    def get_HTML(self, url):
        return self.get(url).text

    def post_JSON(self, url, payload):
        self.logger('POST {}'.format(url))

        r = self.session.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        if r.ok:
            return r.json()
        else:
            self.logger('%s\n%s\n%s' % (r.status_code, r.headers, r.text))
            raise Exception('Failed to POST {}: {}'.format(url, r.status_code))
