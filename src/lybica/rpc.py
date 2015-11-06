import os
import logging
import urllib
import urllib2
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
        if 'method' in kwds:
            method = kwds['method']
            kwds.pop('method')
        else:
            method = None
        logging.info('rpc:%s, method: %s, param:%s' % (api_url, method, str(kwds)))
        response = self._get_response(api_url, kwds, method)
        try:
            return json.loads(response)
        except ValueError:
            logging.info('Error data:%s' % response)
            raise

    @ignore_error(None)
    @retry(5, 5)
    def _get_response(self, api_url, kwds, method=None):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        if kwds:
            request = urllib2.Request(api_url, data=urllib.urlencode(kwds))
            if method is None:
                method = 'POST'
        else:
            request = urllib2.Request(api_url)
        request.set_proxy = lambda x,y: None
        request.get_method = lambda: method or 'GET'
        response = opener.open(request)

        if response.getcode() != 200:
            raise RuntimeError('invalid return code: %d' % opener.getcode())

        return response.read()

