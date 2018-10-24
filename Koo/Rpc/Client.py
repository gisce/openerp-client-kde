import erppeek
from erppeek import Record


def patch_create(self, values, context=None):
    fields = self.fields()
    default_values = self._execute('default_get', fields, context=context)
    if context is None:
        context = self.client.context
    values = self._unbrowse_values(values)
    default_values.update(values)
    patched_values = default_values
    new_id = self._execute('create', patched_values, context=context)
    return Record(self, new_id, context=context)


class Client(object):

    def __new__(cls, session):
        erppeek.Model.create = patch_create
        return erppeek.Client(session.url, session.databaseName, session.userName, session.password)
