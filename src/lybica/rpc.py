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
            return _RestProxy(self.lybica_api_url, name, 'json')
        raise AttributeError('Not found "%s" in AreaCI RPC.' % name)

class _RestProxy(object):
    def __init__(self, base_url, name, context_type='json'):
        self.base = base_url.strip('/')
        self.context_type = context_type
        self.name = name

    def __call__(self, **kwds):
        '''Call remote interface by HTTP'''
        socket.setdefaulttimeout(30)
        api_url = '%s/%s' % (self.base, self.name)
        if 'auto_check' in kwds:
            logging.debug('auto_check set to: %s' % kwds['auto_check'])
            self.auto_check = kwds['auto_check'] == 'true'

        logging.info('rpc:%s, param:%s' % (api_url, str(kwds)))
        response = self._get_response(api_url, kwds)

        if not response:
            raise RuntimeError('Failed to call remote interface, without any response.')

        if self.context_type == 'json':
            try:
                return json.loads(response)
            except ValueError:
                logging.info('Error data:%s' % response)

        return response

    @ignore_error(None)
    @retry(3, 30)
    def _get_response(self, api_url, kwds):
        return urllib.urlopen(api_url, urllib.urlencode(kwds), proxies={}).read()

