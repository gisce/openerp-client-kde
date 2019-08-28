from urllib.parse import urlparse, urljoin
import urllib
import functools
import re
import erppeek
import msgpack


def dispatch_msgpack(url, service_name, method, args):
    endpoint = urljoin(url, service_name)
    m = msgpack.packb([method] + list(args))
    u = urllib.request.urlopen(endpoint, m)
    s = u.read()
    u.close()
    result = msgpack.unpackb(s, raw=False)
    if u.code == 210:
        raise erppeek.ServerError(
            result['exception'],
        )
    return result


class Client(erppeek.Client):
    def __init__(self, session):
        super(Client, self).__init__(session.url, session.databaseName, session.userName, session.password)

    def _proxy_msgpack(self, name):
        return functools.partial(dispatch_msgpack, self._server, name)

    def _set_services(self, server, transport, verbose):
        url = urlparse(server)
        if url.scheme.endswith('+msgpack'):
            self._server = '{}://{}'.format(url.scheme.split('+')[0], url.netloc)
            self._proxy = self._proxy_msgpack

            def get_service(name):
                methods = list(erppeek._methods[name]) if (name in erppeek._methods) else []
                if float_version < 8.0:
                    methods += erppeek._obsolete_methods.get(name) or ()
                return erppeek.Service(self, name, methods, verbose=verbose)

            float_version = 99.0
            self.server_version = ver = get_service('db').server_version()
            self.major_version = re.match(r'\d+\.?\d*', ver).group()
            float_version = float(self.major_version)
            # Create the RPC services
            self.db = get_service('db')
            self.common = get_service('common')
            self._object = get_service('object')
            self._report = get_service(
                'report') if float_version < 11.0 else None
            self._wizard = get_service(
                'wizard') if float_version < 7.0 else None
            self._searchargs = functools.partial(erppeek.searchargs,
                                                 api_v9=(float_version < 10.0))
        else:
            super(Client, self)._set_services(server, transport, verbose)

    def _models_get(self, name):
        try:
            return self._models[name]
        except KeyError:
            self._models[name] = m = Model._new(self, name)
        return m


class Model(erppeek.Model):
    def create(self, values, context=None):
        fields = self.fields()
        default_values = self._execute('default_get', fields, context=context)
        if context is None:
            context = self.client.context
        values = self._unbrowse_values(values)
        default_values.update(values)
        return super(Model, self).create(default_values, values, context)
