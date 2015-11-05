import os
import logging
import urllib
import socket
import json
from .decorators import retry, ignore_error


class RPC(object):
    def __init__(self,):
        self.lybica_api_url = os.getenv('LYBICA_API_URL', '')
        if not self.lybica_api_url:
            raise RuntimeError('Not found ${LYBICA_API_URL} ENV variable.')
        logging.info('LYBICA API URL:%s' % self.lybica_api_url)

    def __getattr__(self, name):
        if not name.startswith('_'):
            if '__' in name:
                name = name.replace('__', '/')
            return _JsonProxy(self.lybica_api_url, name)
        raise AttributeError('Not found "%s" in RPC.' % name)

class _JsonProxy(object):
    def __init__(self, base_url, name):
        self.base = base_url.strip('/')
        self.name = name

    def __call__(self, **kwds):
        '''Call remote interface by HTTP'''
        socket.setdefaulttimeout(30)
        api_url = '%s/%s' % (self.base, self.name)
        logging.info('rpc:%s, param:%s' % (api_url, str(kwds)))
        response = self._get_response(api_url, kwds)
        try:
            return json.loads(response)
        except ValueError:
            logging.info('Error data:%s' % response)
            raise

    @ignore_error(None)
    @retry(3, 30)
    def _get_response(self, api_url, kwds):
        if kwds:
            opener = urllib.urlopen(api_url, urllib.urlencode(kwds), proxies={})
        else:
            opener = urllib.urlopen(api_url, proxies={})

        if opener.getcode() != 200:
            raise RuntimeError('invalid return code: %d' % opener.getcode())

        return opener.read()

