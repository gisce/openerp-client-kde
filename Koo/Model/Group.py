##############################################################################
#
# Copyright (c) 2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
# Copyright (c) 2007-2008 Albert Cervera i Areny <albert@nan-tic.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from Koo.Rpc import RpcProxy
from Koo.Common.Settings import *
from .Record import Record
from . import Field
from PyQt5.QtCore import *


class RecordGroup(QObject):
    """
    # @brief The RecordGroup class manages a list of records.

    Provides functions for loading, storing and creating new objects of the
    same type.The 'fields' property stores a dictionary of dictionaries, each
    of which contains information about a field. This information includes the
    data type ('type'), its name ('name') and other attributes. The
    'fieldObjects' property stores the classes responsible for managing the
    values which are finally stored on the 'values' dictionary in the Model

    The group can also be sorted by any of it's fields. Two sorting methods
    are provided:
    SortVisibleItems and SortAllItems.
    SortVisibleItems is usually faster for a small number of elements as
    sorting is handled on the client side, but only those loaded are
    considered in the sorting. SortAllItems, sorts items in the server so all
    items are considered. Although this would cost a lot when there are
    thousands of items, only some of them are loaded and the rest are loaded on
    demand.

    Note that by default the group will handle (and eventually load) all
    records that match the conditions imposed by 'domain' and 'filter'. Those
    are empty by default so creating RecordGroup('res.parnter') and iterating
    through it's items will return all partners in the database. If you want to
    ensure that the group is kept completely empty, you can call
    setAllowRecordLoading( False ) which is equivalent to calling setFilter()
    with a filter that no records match, but without the overhead of querying
    the server.

    RecordGroup will emit several kinds of signals on certain events.
    """
    recordsInserted = pyqtSignal(int, int)
    recordsRemoved = pyqtSignal(int, int)
    recordChangedSignal = pyqtSignal('PyQt_PyObject')
    # recordChanged = pyqtSignal(QObject)
    _modified = False
    modified = pyqtSignal()
    # @xtorello toreview signal int type
    sorting = pyqtSignal(int)

    SortVisibleItems = 1
    SortAllItems = 2

    SortingPossible = 0
    SortingNotPossible = 1
    SortingOnlyGroups = 2
    SortingNotPossibleModified = 3

    def __init__(self, resource, fields=None, ids=None, parent=None,
                 context=None):
        """
        Creates a new RecordGroup object.

        :param resource: Name of the model to load. Such as 'res.partner'.
        :param fields: Dictionary with the fields to load. This value typically
        comes from the server.
        :param ids: Record identifiers to load in the group.
        :param parent: Only used if this RecordGroup serves as a relation to
        another model. Otherwise it's None.
        :param context: context Context for RPC calls.
        """

        QObject.__init__(self)
        if ids is None:
            ids = []
        if context is None:
            context = {}
        self.parent = parent
        self._context = context
        self._context.update(Rpc.session.context)
        self.resource = resource
        self.limit = Settings.value('koo.limit', 80, int)
        self.maximumLimit = self.limit
        self.rpc = RpcProxy(resource)

        if fields is None:
            self.fields = {}
        else:
            self.fields = fields
        self.fieldObjects = {}
        self.loadFieldObjects(list(self.fields.keys()))

        self.records = []

        # @xtorello toreview signal to method integration
        # self.recordChangedSignal.connect(self.recordChanged)

        self.enableSignals()

        # toBeSorted properties store information each time sort() function
        # is called. If loading of records is not enabled, records won't be
        # loaded but we keep by which field we want information to be sorted
        # so when record loading is enabled again we know how should the sorting
        # be.
        self.toBeSortedField = None
        self.toBeSortedOrder = None

        self.sortedField = None
        self.sortedOrder = None
        self.updated = False
        self._domain = []
        self._filter = []

        if Settings.value('koo.sort_mode') == 'visible_items':
            self._sortMode = self.SortVisibleItems
        else:
            self._sortMode = self.SortAllItems
        self._sortMode = self.SortAllItems

        self._allFieldsLoaded = False

        self.load(ids)
        self.removedRecords = []
        self._onWriteFunction = ''

    def setLoadOneByOne(self, value):
        """
        Sets wether data loading should be done on record chunks or one by one.

        Setting value to True, will make the RecordGroup ignore the current
        'limit' property, and load records by one by, instead. If set to
        False (the default) it will load records in groups of 'limit'
        (80, by default).

        In some cases (widgets that show multiple records) it's better to load
        in chunks, in other cases, it's better to load one by one.
        :param value:
        :return: None
        :rtype: None
        """
        if value:
            self.limit = 1
        else:
            self.limit = self.maximumLimit

    def setSortMode(self, mode):
        self._sortMode = mode

    def sortMode(self):
        return self._sortMode

    def setOnWriteFunction(self, value):
        self._onWriteFunction = value

    def onWriteFunction(self):
        return self._onWriteFunction

    def __del__(self):
        if self.parent:
            try:
                self.modified.disconnect()
                self.tomanyfield = None
            except Exception:
                pass

        self.rpc = None
        self.parent = None
        self.resource = None
        self._context = None
        self.fields = None
        for r in self.records:
            if not isinstance(r, Record):
                continue

            try:
                r.recordChanged.disconnect()
            except Exception:
                pass

            r.__del__()
        self.records = []
        for f in self.fieldObjects:
            try:
                self.fieldObjects[f].parent = None
                self.disconnect()
            except Exception:
                pass

            # @xtorello toreview
            #self.fieldObjects[f].setParent(None)
            #self.fieldObjects[f].__del__()
            #self.disconnect( self.fieldObjects[f], None, 0, 0 )
            #self.fieldObjects[f] = None
            #del self.fieldObjects[f]
        self.fieldObjects = {}

    def fieldType(self, fieldName):
        """
        Returns a string with the name of the type of a given field. Such as
        'char'.

        :param fieldName: Name of the field
        :type fieldName: str
        :return: Field type
        :rtype: str
        """
        if not fieldName in self.fields:
            return None
        return self.fields[fieldName]['type']

    def loadFieldObjects(self, fkeys):
        """
        Creates the entries in 'fieldObjects' for each key of the 'fkeys' list.
        :param fkeys:
        :return: None
        :rtype: None
        """
        for fname in fkeys:
            fvalue = self.fields[fname]
            fvalue['name'] = fname
            self.fieldObjects[fname] = Field.FieldFactory.create(
                fvalue['type'], self, fvalue)
            if fvalue['type'] in ('binary', 'image'):
                val = Field.FieldFactory.create('binary-size', self, fvalue)
                self.fieldObjects['%s.size' % fname] = val

    def save(self):
        """
        Saves all the records.

        Note that there will be one request to the server per modified or
        created record.

        :return:
        """

        for record in self.records:
            if isinstance(record, Record):
                record.save()

    def modifiedRecords(self):
        """
        Returns a list with all modified records

        :return: None
        :rtype: None
        """
        modified = []
        for record in self.records:
            if isinstance(record, Record) and record.isModified():
                modified.append(record)
        return modified

    def written(self, editedId):
        """
        This function executes the 'onWriteFunction' function in the server.

        If there is a 'onWriteFunction' function associated with the model type
        handled by this record group it will be executed. 'editedId' should
        provide the id of the just saved record.

        This functionality is provided here instead of on the record because
        the remote function might update some other records, and they need to
        be (re)loaded.

        :param editedId:
        :return:
        """
        if not self._onWriteFunction or not editedId:
            return
        # Execute the onWriteFunction function on the server.
        # It's expected it'll return a list of ids to be loaded or reloaded.
        new_ids = getattr(self.rpc, self._onWriteFunction)(
            editedId, self.context())
        record_idx = self.records.index(self.recordById(editedId))
        result = False
        indexes = []
        for id in new_ids:
            cont = False
            for m in self.records:
                if isinstance(m, Record):
                    if m.id == id:
                        cont = True
                        # TODO: Shouldn't we just call cancel() so the record
                        # is reloaded on demand?
                        m.reload()
            if cont:
                continue
            # TODO: Should we reconsider this? Do we need/want to reload.
            # Probably we only want to add the id to the list.
            record = Record(id, self, parent=self.parent)
            record.recordChanged['PyQt_PyObject'].connect(self.recordChanged)
            record.recordModified['PyQt_PyObject'].connect(self.recordModified)
            record.reload()
            if not result:
                result = record
            newIndex = min(record_idx, len(self.records) - 1)
            self.add(record, newIndex)
            indexes.append(newIndex)

        if indexes:
            self.recordsInserted.emit(min(indexes), max(indexes))
        return result

    def loadFromValues(self, values):
        """
        Adds a list of records as specified by 'values'.

        :param values: 'values' has to be a list of dictionaries, each of which
        containing fields names -> values. At least key 'id' needs to be in
        all dictionaries.
        :return: None
        :rtype: None
        """
        start = len(self.records)
        for value in values:
            record = Record(value['id'], self, parent=self.parent)
            record.set(value)
            self.records.append(record)
            record.recordChanged['PyQt_PyObject'].connect(self.recordChanged)
            record.recordModified['PyQt_PyObject'].connect(self.recordModified)
        end = len(self.records) - 1
        self.recordsInserted.emit(start, end)

    def load(self, ids, addOnTop=False):
        """
        Creates as many records as len(ids) with the ids[x] as id.

        'ids' needs to be a list of identifiers. The addFields() function
        can be used later to load the necessary fields for each record.

        :param ids:
        :type ids: list(int)
        :param addOnTop:
        :return: None
        :rtype: None
        """

        if not ids:
            return
        if addOnTop:
            start = 0
            # Discard from 'ids' those that are already loaded.
            # If we didn't do that, some records could be repeated if the
            # programmer doesn't verify that, and we'd end up in errors
            # because when records are actually loaded they're only checked
            # against a single appearance of the id in the list of records.
            #
            # Note we don't use sets to discard ids, because we want to keep
            # the order their order and because it can cause infinite recursion.
            currentIds = self.ids()
            for ident in ids:
                if ident not in currentIds:
                    self.records.insert(0, ident)
            end = len(ids) - 1
        else:
            start = len(self.records)
            # Discard from 'ids' those that are already loaded. Same as above.
            currentIds = self.ids()
            for ident in ids:
                if ident not in currentIds:
                    self.records.append(ident)
            end = len(self.records) - 1
        # We consider the group is updated because otherwise calling count()
        # would force an update() which would cause one2many relations to
        # load elements when we only want to know how many are there.
        self.updated = True
        self.recordsInserted.emit(start, end)

    def clear(self):
        """
        Clears the list of records. It doesn't remove them.
        :return:
        """
        for record in self.records:
            if isinstance(record, Record):
                record.recordChanged['PyQt_PyObject'].disconnect(self.recordChanged)
                record.recordModified['PyQt_PyObject'].disconnect(self.recordModified)
        last = len(self.records) - 1
        self.records = []
        self.removedRecords = []
        self.recordsRemoved.emit(0, last)

    def context(self):
        """
        Returns a copy of the current context

        :return: Current context copy
        :rtype: dict
        """
        ctx = {}
        ctx.update(self._context)
        return ctx

    def setContext(self, context):
        """
        Sets the context that will be used for RPC calls.
        :param context:
        :return:
        """
        self._context = context.copy()

    def add(self, record, position=-1):
        """
        Adds a record to the list
        :param record:
        :param position:
        :return:
        """
        if not record.group is self:
            fields = {}
            for mf in record.group.fields:
                fields[record.group.fields[mf]['name']
                       ] = record.group.fields[mf]
            self.addFields(fields)
            record.group.addFields(self.fields)
            record.group = self

        if position == -1:
            self.records.append(record)
        else:
            self.records.insert(position, record)
        record.parent = self.parent
        record.recordChanged['PyQt_PyObject'].connect(self.recordChanged)
        record.recordModified['PyQt_PyObject'].connect(self.recordModified)
        return record

    def create(self, default=True, position=-1, domain=None, context=None):
        """
        Creates a new record of the same type of the records in the group.

        If 'default' is true, the record is filled in with default values.
        'domain' and 'context' are only used if default is true.
        :param default:
        :param position:
        :param domain:
        :param context:
        :return:
        """
        if domain is None:
            domain = []
        if context is None:
            context = {}
        self.ensureUpdated()

        record = Record(None, self, parent=self.parent, new=True)
        if default:
            ctx = context.copy()
            ctx.update(self.context())
            record.fillWithDefaults(domain, ctx)
        self.add(record, position)
        if position == -1:
            start = len(self.records) - 1
        else:
            start = position
        self.recordsInserted.emit(start, start)
        return record

    def disableSignals(self):
        self._signalsEnabled = False

    def enableSignals(self):
        self._signalsEnabled = True

    @pyqtSlot('PyQt_PyObject')
    def recordChanged(self, record):
        if self._signalsEnabled:
            self.recordChangedSignal.emit(record)
        if self.parent:
            self.recordChangedSignal.emit(self.parent)

    def recordModified(self, record, many2many=False):
        # whole group marked as modified when adding/removing items in many2many
        if many2many:
            self._modified = True
        if self._signalsEnabled:
            self.modified.emit()
        if self.parent:
            self.parent.recordModified.emit(self.parent)

    def removeRecord(self, record):
        """
        Removes a record from the record group but not from the server.

        If the record doesn't exist it will ignore it silently.
        :param record:
        :return: None
        :rtype: None
        """

        idx = self.records.index(record)
        if isinstance(record, Record):
            ident = record.id
        else:
            ident = record
        if id:
            # Only store removedRecords if they have a valid Id.
            # Otherwise we don't need them because they don't have
            # to be removed in the server.
            self.removedRecords.append(ident)
        if isinstance(record, Record):
            if record.parent:
                record.parent.modified = True
        self.freeRecord(record)
        self.modified.emit()
        self.recordsRemoved.emit(idx, idx)

    def removeRecords(self, records):
        """
        Remove a list of records from the record group but not from the server.

        If a record doesn't exist it will ignore it silently.
        :param records:
        :type records: list(Record)
        :return: None
        :rtype: None
        """

        firstIdx = -1
        lastIdx = -1
        toRemove = []
        for record in records:
            if not record in records:
                continue
            idx = self.records.index(record)
            if firstIdx < 0 or idx < firstIdx:
                firstIdx = idx
            if lastIdx < 0 or idx > lastIdx:
                lastIdx = idx
            if isinstance(record, Record):
                ident = record.id
            else:
                ident = record
            if ident:
                # Only store removedRecords if they have a valid Id.
                # Otherwise we don't need them because they don't have
                # to be removed in the server.
                self.removedRecords.append(ident)
            if isinstance(record, Record):
                if record.parent:
                    record.parent.modified = True
            self.freeRecord(record)
        self.modified.emit()
        self.recordsRemoved.emit(firstIdx, lastIdx)

    def remove(self, record):
        """
        Removes a record from the record group but not from the server.

        If the record doesn't exist it will ignore it silently.
        :param record:
        :return:
        """
        if isinstance(record, list):
            self.removeRecords(record)
        else:
            self.removeRecord(record)

    def binaryFieldNames(self):
        return [x[:-5] for x in list(self.fieldObjects.keys()) if x.endswith('.size')]

    def allFieldNames(self):
        return [x for x in list(self.fieldObjects.keys()) if not x.endswith('.size')]

    def createAllFields(self):
        if self._allFieldsLoaded:
            return
        fields = self.rpc.fields_get()
        self.addFields(fields)
        self._allFieldsLoaded = True

    def addFields(self, fields):
        """
        Adds the specified fields to the record group

        Note that it updates 'fields' and 'fieldObjects' in the group.
        'fields' is a dict of dicts as typically returned by 'fields_get'
        server function.
        :param fields:
        :return:
        """
        to_add = []
        for f in list(fields.keys()):
            if not f in self.fields:
                self.fields[f] = fields[f]
                self.fields[f]['name'] = f
                to_add.append(f)
            else:
                self.fields[f].update(fields[f])
        self.loadFieldObjects(to_add)
        return to_add

    def ensureAllLoaded(self):
        """
        Ensures all records in the group are loaded.
        :return: None
        :rtype: None
        """
        ids = self.unloadedIds()
        if not ids:
            return
        c = Rpc.session.context.copy()
        c.update(self.context())
        c['bin_size'] = True
        values = self.rpc.read(ids, list(self.fields.keys()), c)
        if values:
            for v in values:
                #self.recordById( v['id'] ).set(v, signal=False)
                r = self.recordById(v['id'])
                r.set(v, signal=False)

    def unloadedIds(self):
        """
        Returns the list of ids that have not been loaded yet. The list
        won't include new records as those have id 0 or None.
        :return: List of ids
        :rtype: list(int)
        """
        self.ensureUpdated()
        ids = []
        for x in self.records:
            if isinstance(x, Record):
                if x.id and not x._loaded:
                    ids.append(x.id)
            elif x:
                ids.append(x)
        return ids

    def loadedRecords(self):
        """
        Returns the list of loaded records. The list won't include new records.
        :return: List of loaded records
        :rtype: list(int)
        """
        records = []
        for x in self.records:
            if isinstance(x, Record):
                if x.id and x._loaded:
                    records.append(x)
        return records

    def ids(self):
        """
        Returns a list with all ids.
        :return:
        :rtype: list
        """
        ids = []
        for x in self.records:
            if isinstance(x, Record):
                ids.append(x.id)
            else:
                ids.append(x)
        return ids

    def newRecords(self):
        """
        Returns a list with all new records.
        :return:
        :rtype: list
        """
        records = []
        for x in self.records:
            if not isinstance(x, Record):
                continue
            if x.id:
                continue
            records.append(x)
        return records

    def count(self):
        """
        Returns the number of records in this group.
        :return: Number of records in this group.
        :rtype: int
        """
        self.ensureUpdated()
        return len(self.records)

    def __iter__(self):
        self.ensureUpdated()
        self.ensureAllLoaded()
        return iter(self.records)

    def modelById(self, ident):
        """
        Returns the record with id 'id'. You can use [] instead.
        Note that it will check if the record is loaded and load it if not.
        :param ident:
        :return:
        """
        record = self.recordById(ident)
        if not record:
            return None
        return record
    __getitem__ = modelById

    def modelByIndex(self, row):
        """
        Returns the record at the specified row number.
        :param row:
        :return:
        """
        record = self.recordByIndex(row)
        return record

    def indexOfRecord(self, record):
        """
        Returns the row number of the given record. Note that
        the record must be in the group. Otherwise an exception is risen.
        :param record:
        :return:
        """
        if record in self.records:
            return self.records.index(record)
        else:
            return -1

    def indexOfId(self, ident):
        """
        Returns the row number of the given id.
        If the id doesn't exist it returns -1.
        :param ident:
        :return: Row number of the id, if no exists -1
        :rtype: int
        """
        i = 0
        for record in self.records:
            if isinstance(record, Record):
                if record.id == ident:
                    return i
            elif record == ident:
                return i
            i += 1
        return -1

    def recordExists(self, record):
        """
        Returns True if the given record exists in the group.
        :param record:
        :return:
        """
        return record in self.records

    def fieldExists(self, fieldName):
        """
        Returns True if the given field name exists in the group.
        :param fieldName:
        :return:
        """
        return fieldName in self.fieldObjects

    def recordById(self, id):
        """
        Returns the record with id 'id'. You can use [] instead. Note that it
        will return the record but won't try to load it.

        :param id: Record id
        :type id: int
        :return: record
        :rtype: Record
        """
        for record in self.records:
            if isinstance(record, Record):
                if record.id == id:
                    return record
            elif record == id:
                idx = self.records.index(id)
                record = Record(id, self, parent=self.parent)
                record.recordChanged['PyQt_PyObject'].connect(self.recordChanged)
                record.recordModified['PyQt_PyObject'].connect(self.recordModified)
                self.records[idx] = record
                return record

    def duplicate(self, record):
        if record.id:
            # If record exists in the database, ensure we copy all fields.
            self.createAllFields()
            self.ensureRecordLoaded(record)

        newRecord = self.create()
        newRecord.values = record.values.copy()
        for field in list(newRecord.values.keys()):
            if self.fieldType(field) in ('one2many'):
                del newRecord.values[field]
        newRecord.modified = True
        newRecord.changed()
        return newRecord

    def recordByIndex(self, row):
        """
        Returns a Record object for the given row.
        :param row:
        :return:
        """
        record = self.records[row]
        if isinstance(record, Record):
            return record
        else:
            record = Record(record, self, parent=self.parent)
            record.recordChanged['PyQt_PyObject'].connect(self.recordChanged)
            record.recordModified['PyQt_PyObject'].connect(self.recordModified)
            self.records[row] = record
            return record

    def isWizard(self):
        """
        Returns True if the RecordGroup handles information of a wizard.
        :return:
        """
        return self.resource.startswith('wizard.')

    def ensureRecordLoaded(self, record):
        """
        Checks whether the specified record is fully loaded and loads
        it if necessary.

        :param record:
        :return: None
        :rtype: None
        """

        self.ensureUpdated()
        # Do not try to load if record is new.
        if not record.id:
            record.createMissingFields()
            return
        if record.isFullyLoaded():
            return

        c = Rpc.session.context.copy()
        c.update(self.context())
        ids = self.ids()
        pos = ids.index(record.id) / self.limit

        queryIds = ids[int(pos * self.limit): int(pos * self.limit) + self.limit]
        if None in queryIds:
            queryIds.remove(None)

        missingFields = record.missingFields()

        self.disableSignals()
        c['bin_size'] = True
        values = self.rpc.read(queryIds, missingFields, c)
        if values:
            for v in values:
                ident = v['id']
                if 'id' not in missingFields:
                    del v['id']
                self.recordById(ident).set(v, signal=False)
        self.enableSignals()
        # TODO: Take a look if we need to set default values for new records!
        # Set defaults
        # if len(new) and len(to_add):
        #values = self.rpc.default_get( to_add, self.context() )
        # for t in to_add:
        # if t not in values:
        #values[t] = False
        # for mod in new:
        # mod.setDefaults(values)

    def setDomain(self, value):
        """
        Allows setting the domain for this group of records.
        :param value:
        :return:
        """
        # In some (rare) cases we receive {} as domain. So let's just test
        # 'not value', and that should work in all cases, not only when value
        # is None.
        if not value:
            self._domain = []
        else:
            self._domain = value
        if Settings.value('koo.load_on_open', True):
            self.updated = False

    def domain(self):
        """
        Returns the current domain.
        :return:
        """
        return self._domain

    def setFilter(self, value):
        """
        Allows setting a filter for this group of records.

        The filter is conatenated to the domain to further restrict the records
        of the group.
        :param value: value of the filter
        :return: None
        :rtype: None
        """
        if value == None:
            self._filter = []
        else:
            self._filter = value
        self.updated = False

    # @brief
    def filter(self):
        """
        Returns the current filter.
        :return:
        """
        return self._filter

    def setDomainForEmptyGroup(self):
        """
        Disables record loading by setting domain to [('id','in',[])]

        RecordGroup will optimize the case when domain + filter =
        [('id','in',[])] by not even querying the server and searching ids. It
        will simply consider the result is [] and thus the group will be kept
        empty.

        Domain may be changed using setDomain() function.
        :return:
        """
        if self.isModified():
            return
        self.setDomain([('id', 'in', [])])
        self.clear()

    def isDomainForEmptyGroup(self):
        """
        Returns True if domain is [('id','in',[])]
        :return:
        """
        return self.domain() == [('id', 'in', [])]

    def update(self):
        """
        Reload the record group with current selected sort field, order,
        domain and filter
        :return:
        """

        # Update context from Rpc.session.context as language
        # (or other settings) might have changed.
        self._context.update(Rpc.session.context)
        self.rpc = RpcProxy(self.resource)
        # Make it reload again
        self.updated = False
        self.sort(self.toBeSortedField, self.toBeSortedOrder)

    def ensureUpdated(self):
        """
        Ensures the group is updated.
        :return: None
        :rtype: None
        """

        if self.updated:
            return
        self.update()

    def sort(self, field, order):
        """
        Sorts the group by the given field name.

        :param field:
        :param order:
        :return:
        """
        self.toBeSortedField = field
        self.toBeSortedOrder = order
        if self._sortMode == self.SortAllItems:
            self.sortAll(field, order)
        else:
            self.sortVisible(field, order)

    def sortAll(self, field, order):
        """
        Sorts the records in the group using ALL records in the database
        :param field:
        :param order:
        :return:
        """
        if self.updated and field == self.sortedField and order == self.sortedOrder:
            return

        # Check there're no new or modified records. If there are
        # we won't sort as it means reloading data from the server
        # and we'd loose current changes.
        if self.isModified():
            self.sorting.emit(self.SortingNotPossibleModified)
            return

        oldSortedField = self.sortedField

        # We set this fields in the very beggining in case some signals are cought
        # and retry to sort again which would cause an infinite recursion.
        self.sortedField = field
        self.sortedOrder = order
        self.updated = True

        sorted = False
        sortingResult = self.SortingPossible

        if self._domain + self._filter == [('id', 'in', [])]:
            # If setDomainForEmptyGroup() was called, or simply the domain
            # included no tuples, we don't even need to query the server.
            # Note that this may be quite important in some wizards because
            # the model will actually not exist in the server and would raise
            # an exception.
            ids = []
        elif not field in list(self.fields.keys()):
            # If the field doesn't exist use default sorting. Usually this will
            # happen when we update and haven't selected a field to sort by.
            ids = self.rpc.search(
                self._domain + self._filter, 0, False, False, self._context)
        else:
            field_type = self.fields[field]['type']
            if field_type == 'one2many' or type == 'many2many':
                # We're not able to sort 2many fields
                sortingResult = self.SortingNotPossible
            elif field_type == 'many2one':
                # This works only if '#407667' is fixed, but it was fixed in
                # 2010-02-03
                orderby = '"%s"' % field
                if order == Qt.AscendingOrder:
                    orderby += " ASC"
                else:
                    orderby += " DESC"
                try:
                    ids = Rpc.session.call(
                        '/koo', 'search',
                        self.resource,
                        self._domain + self._filter, 0, 0, orderby,
                        self._context
                    )
                    sortingResult = self.SortingPossible
                    sorted = True
                except:
                    sortingResult = self.SortingOnlyGroups

            # We check whether the field is stored or not. In case the server
            # is not _ready_ we consider it's stored and we'll catch the
            # exception later.
            stored = self.fields[field].get('stored', True)
            if not stored:
                sortingResult = self.SortingNotPossible

            if not sorted and sortingResult != self.SortingNotPossible:
                # A lot of the work done here should be done on the server by
                # core OpenERP functions. This means this runs slower than it
                # should due to network and serialization latency. Even more,
                # we lack some information to make it work well.

                # Ensure the field is quoted, otherwise fields such as 'to'
                # can't be sorted and return an exception.
                orderby = '"%s"' % field
                if order == Qt.AscendingOrder:
                    orderby += " ASC"
                else:
                    orderby += " DESC"

                try:
                    # Use call to catch exceptions
                    ids = Rpc.session.call(
                        '/object', 'execute', self.resource, 'search',
                        self._domain + self._filter, 0, 0, orderby,
                        self._context)
                except Exception:
                    # In functional fields not stored in the database this will
                    # cause an exception :(
                    sortingResult = self.SortingNotPossible

        if sortingResult != self.SortingNotPossible:
            self.clear()
            # The load function will be in charge of loading and sorting
            # elements
            self.load(ids)
        elif oldSortedField == self.sortedField or not self.ids():
            # If last sorted field was the same as the current one, possibly
            # only filter crierias have changed so we might need to reload in
            # this case.
            # If sorting is not possible, but no data was loaded yet, we load
            # by model default field and order. Otherwise, a view might not
            # load any data.
            ids = self.rpc.search(
                self._domain + self._filter, 0, 0, False, self._context)
            self.clear()
            # The load function will be in charge of loading and sorting
            # elements
            self.load(ids)

        self.sorting.emit(sortingResult)

    def sortVisible(self, field, order):
        """
        Sorts the records of the group taking into account only loaded fields.
        :param field:
        :param order:
        :return:
        """
        if self.updated and field == self.sortedField and order == self.sortedOrder:
            return

        if not self.updated:
            ids = self.rpc.search(
                self._domain + self._filter, 0, self.limit, False, self._context)
            self.clear()
            self.load(ids)

        if not field in self.fields:
            return

        self.ensureAllLoaded()

        if field != self.sortedField:
            # Sort only if last sorted field was different than current

            # We need this function here as we use the 'field' variable
            def ignoreCase(record):
                v = record.value(field)
                if isinstance(v, str) or isinstance(v, str):
                    return v.lower()
                else:
                    return v

            field_type = self.fields[field]['type']
            if field_type == 'one2many' or field_type == 'many2many':
                self.records.sort(key=lambda x: len(x.value(field).group))
            else:
                self.records.sort(key=ignoreCase)
            if order == Qt.DescendingOrder:
                self.records.reverse()
        else:
            # If we're only reversing the order, then reverse simply reverse
            if order != self.sortedOrder:
                self.records.reverse()

        self.sortedField = field
        self.sortedOrder = order
        self.updated = True

        # Emit recordsInserted() to ensure KooModel is updated.
        self.recordsInserted.emit(0, len(self.records) - 1)

        self.sorting.emit(self.SortingPossible)

    # @brief Removes all new records and marks all modified ones as not loaded.
    def cancel(self):
        for record in self.records[:]:
            if isinstance(record, Record):
                if not record.id:
                    self.freeRecord(record)
                elif record.isModified():
                    record.cancel()
            else:
                if not record:
                    self.freeRecord(record)

    def freeRecord(self, record):
        """
        Removes a record from the list (but not the record from the database).

        This function is used to take care signals are disconnected.
        :param record:
        :return:
        """
        self.records.remove(record)
        if isinstance(record, Record):
            record.recordChanged['PyQt_PyObject'].disconnect(self.recordChanged)
            record.recordModified['PyQt_PyObject'].disconnect(self.recordModified)

    def isModified(self):
        """
        Returns True if any of the records in the group has been modified.
        :return: True if any of the records in the group has been modified.
        :rtype: bool
        """
        if self._modified:
            return True
        for record in self.records:
            if isinstance(record, Record):
                if record.isModified():
                    return True
        return False

    def isRecordModified(self, ident):
        """
        Returns True if the given record has been modified.
        :param id:
        :return:
        """
        for record in self.records:
            if isinstance(record, Record):
                if record.id == ident:
                    return record.isModified()
            elif record == ident:
                return False
        return False

    def isFieldRequired(self, fieldName):
        """
        Returns True if the given field is required in the RecordGroup,
        otherwise returns False.
        Note that this is a flag for the whole group, but each record could
        have different values depending on its state.
        :param fieldName:
        :return:
        """
        required = self.fields[fieldName].get('required', False)
        if isinstance(required, bool):
            return required
        if isinstance(required, str) or isinstance(required, str):
            if required.lower() == 'true':
                return True
            if required.lower() == 'false':
                return False
        return bool(int(required))


# vim:noexpandtab:
