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

import re
import time
from Koo import Rpc
from Koo.Common import Notifier
from Koo.Rpc import RpcProxy
from .Field import ToManyField
from Koo.Common import Debug

from PyQt5.QtCore import *

# ConcurrencyCheckField = '__last_update'
ConcurrencyCheckField = 'read_delta'


class EvalEnvironment(object):
    def __init__(self, parent):
        self.parent = parent

    def __getattr__(self, item):
        if item == 'parent' and self.parent.parent:
            return EvalEnvironment(self.parent.parent)
        if item == "current_date":
            return time.strftime('%Y-%m-%d')
        if item == "time":
            return time
        return self.parent.get(includeid=True)[item]

    def __del__(self):
        self.parent = None

# We inherit QObject as we'll be using signals & slots


class Record(QObject):
    recordChanged = pyqtSignal('PyQt_PyObject')
    recordModified = pyqtSignal('PyQt_PyObject')
    setFocus = pyqtSignal('QString')

    def __init__(self, ident, group, parent=None, new=False):
        QObject.__init__(self, group)
        self.rpc = group.rpc
        self.id = ident
        self._loaded = False
        self.parent = parent
        self.group = group
        self.values = {}
        self._stateAttributes = {}
        self.modified = False
        self.modified_fields = {}
        self.invalidFields = []
        self.read_time = time.time()
        self.new = new

    def __del__(self):
        self.rpc = None
        self.modified_fields = None
        self.parent = None
        self.setParent(None)
        for key, value in self.values.items():
            from .Group import RecordGroup
            if isinstance(value, RecordGroup):
                try:

                    value.parent.fields()[key].disconnect()
                    value.__del__()
                except Exception:
                    pass

        self.values = {}
        self.invalidFields = []
        if self.id == 2:
            Debug.printReferrers(self)
        self.group = None

    def _getModified(self):
        return self._modified

    def _setModified(self, value):
        self._modified = value
    modified = property(_getModified, _setModified)

    def __getitem__(self, name):
        return self.group.fieldObjects.get(name, False)

    def __repr__(self):
        return '<Record %s>' % self.id

    def setValue(self, fieldName, value):
        """
        Establishes the value for a given field

        :param fieldName:
        :param value:
        :return: None
        """

        record = self
        if not fieldName in self.values:
            self.group.ensureRecordLoaded(self)
            x = 0
            while self.group.records[x].id != self.id:
                x += 1
            record = self.group.records[x]
        self.group.fieldObjects[fieldName].set_client(record, value)

    def value(self, fieldName):
        """
        Obtains the value of a given field

        :param fieldName: Name of the field
        :type fieldName: str
        :return: Value of the field
        :rtype: int, list, tuple
        """
        record = self
        field = self.group.fieldObjects[fieldName]
        if fieldName not in self.values:
            self.group.ensureRecordLoaded(self)
            x = 0
            while self.group.records[x] != self.id:
                x += 1
            record = self.group.records[x]
        return field.get_client(record)

    def setDefault(self, fieldName, value):
        """
        Establishes the default value for a given field

        :param fieldName:
        :param value:
        :return: None
        """

        self.group.fieldObjects[fieldName].set_client(self, value)

    def default(self, fieldName):
        """
        Obtains the default value of a given field

        :param fieldName:
        :type fieldName: str
        :return:
        """
        return self.group.fieldObjects[fieldName].default(self)

    def domain(self, fieldName):
        """
        Obtains the domain of the given field
        :param fieldName:
        :type fieldName: str
        :return:
        """
        return self.group.fieldObjects[fieldName].domain(self)

    def fieldContext(self, fieldName):
        """
        Obtains the context of the given field
        :param fieldName:
        :type fieldName: str
        :return:
        """
        # Do not checkLoad because current record is already loaded and using it
        # would cause all related (one2many and many2many) fields to be
        # completely loaded too, causing performance issues.
        return self.group.fieldObjects[fieldName].context(self, checkLoad=False)

    def isModified(self):
        """
        Returns whether the record has been modified or not
        :return: True if  the record been modified
        :rtype: bool
        """
        mod = self.modified
        for key_name, value in self.values.items():
            from .Group import RecordGroup
            if isinstance(value, RecordGroup):
                if value.isModified():
                    mod = True
        return mod

    def fields(self):
        return self.group.fieldObjects

    def modifiedFields(self):
        return list(self.modified_fields.keys())

    def stateAttributes(self, fieldName):
        if fieldName not in self._stateAttributes:
            if fieldName in self.group.fieldObjects:
                # @xtorello toreview
                # self._stateAttributes[fieldName] = {}
                self._stateAttributes[fieldName] = self.group.fieldObjects[fieldName].attrs.copy()
            else:
                self._stateAttributes[fieldName] = {}
        return self._stateAttributes[fieldName]

    def setStateAttributes(self, fieldName, state='draft'):
        # @xtorello toreview
        field = self.group.fieldObjects[fieldName]
        stateChanges = dict(field.attrs.get('states', {}).get(state[0], []))
        for key in ('readonly', 'required'):
            if key in stateChanges:
                self.stateAttributes(fieldName)[key] = stateChanges[key]
            else:
                self.stateAttributes(fieldName)[key] = field.attrs.get(
                    key, False
                )

    def updateStateAttributes(self):
        state = self.values.get('state', 'draft')
        if not state:
            state = 'draft'
        for key in self.group.fieldObjects:
            self.setStateAttributes(key, state)

    def updateAttributes(self):
        self.updateStateAttributes()
        for fieldName in self.group.fieldObjects:
            # @xtorello toreview
            attributes = self.group.fieldObjects[fieldName].attrs.get(
                'attrs', '{}'
            )

            try:
                attributeChanges = eval(attributes)
            except:
                attributeChanges = eval(attributes, self.value(fieldName))

            for attribute, condition in list(attributeChanges.items()):
                for i in range(0, len(condition)):
                    if len(condition[i]) >= 3 and condition[i][2] and isinstance(condition[i][2], list):
                        attributeChanges[attribute][i] = (
                            condition[i][0], condition[i][1], condition[i][2][0])
            for attribute, condition in attributeChanges.items():
                value = self.evaluateCondition(condition)
                if value:
                    self.stateAttributes(fieldName)[attribute] = value

    def isFieldReadOnly(self, fieldName):
        readOnly = self.stateAttributes(fieldName).get('readonly', False)
        if isinstance(readOnly, bool):
            return readOnly
        if isinstance(readOnly, str) or isinstance(readOnly, str):
            readOnly = readOnly.strip()
            if readOnly.lower() == 'true' or readOnly == '1':
                return True
            if readOnly.lower() == 'false' or readOnly == '0':
                return False
        return bool(readOnly)

    def isFieldRequired(self, fieldName):
        required = self.stateAttributes(fieldName).get('required', False)
        if isinstance(required, bool):
            return required
        if isinstance(required, str) or isinstance(required, str):
            required = required.strip()
            if required.lower() == 'true' or required == '1':
                return True
            if required.lower() == 'false' or required == '0':
                return False
        return bool(required)

    def fieldExists(self, fieldName):
        """
        Returns True if the given field name exists in record's group.
        :param fieldName:
        :type fieldName: str
        :return:
        """
        return fieldName in self.group.fieldObjects

    def ensureIsLoaded(self):
        """
        Loads the record if it's not been loaded already.
        :return: True if is reloaded
        :rtype: bool
        """
        if not self._loaded:
            self.reload()
            return True
        return False

    def get(self, get_readonly=True, includeid=False, checkLoad=True,
            get_modifiedonly=False):
        if checkLoad:
            self.ensureIsLoaded()
        value = {}

        # Iterate over self.group.fields to avoid objects of type
        # BinarySizeField which shouldn't be treated as a normal field.
        for name in self.group.fields:
            if not name in self.values:
                continue

            field = self.group.fieldObjects[name]
            # The record may not have all the fields the group has.
            # This is because there may have been a switch view to a form
            # but not for this record.
            from .Group import RecordGroup
            if isinstance(self.values[name], RecordGroup) and self.values[name].isModified():
                value[name] = field.get(self, readonly=get_readonly, modified=get_modifiedonly)
            elif (get_readonly or not self.isFieldReadOnly(name)) \
                    and (not get_modifiedonly or field.name in self.modified_fields) :
                value[name] = field.get(
                    self, readonly=get_readonly, modified=get_modifiedonly)
        if includeid:
            value['id'] = self.id
        return value

    def cancel(self):
        """
        Marks the current record as not loaded.
        :return: None
        :rtype: None
        """
        self._modified = False
        self._loaded = False

    def save(self, reload=True):
        """
        Save the record to the database. It doesn't matter if the record is
        new or already exists.

        :param reload:
        :return:
        """

        from .Group import RecordGroup

        self.ensureIsLoaded()
        if not self.id:
            value = self.get(get_readonly=False)
            self.id = self.rpc.create(value, self.context())
        else:
            if not self.isModified():
                return self.id
            value = self.get(get_readonly=False, get_modifiedonly=True)
            context = self.context()
            context = context.copy()
            context[ConcurrencyCheckField] = time.time() - self.read_time
            if not self.rpc.write([self.id], value, context):
                return False
        self._loaded = False

        # Delete elements
        for key_name, value in self.values.items():
            if isinstance(value, RecordGroup):
                if value.removedRecords:
                    model = value.resource
                    ids = value.removedRecords
                    Rpc.RpcProxy(model).unlink(ids)
        if reload:
            self.reload()
        if self.group:
            self.group.written(self.id)
        return self.id

    def fillWithDefaults(self, domain=None, context=None):
        """
        Used only by group.py
        Fills the record with the corresponding default values.
        :param domain:
        :param context:
        :return: None
        :rtype: None
        """
        if domain is None:
            domain = []
        if context is None:
            context = {}
        if len(self.group.fields):
            val = self.rpc.default_get(list(self.group.fields.keys()), context)
            for d in domain:
                if d[0] in self.group.fields:
                    if d[1] == '=':
                        val[d[0]] = d[2]
                    elif d[1] == 'in' and len(d[2]) == 1:
                        val[d[0]] = d[2][0]
            self.setDefaults(val)
            self.updateAttributes()

    def name(self):
        """
        Obtains the value of the 'name' field for the record by calling model's
        name_get function in the server.
        :return:
        """

        name = self.rpc.name_get([self.id], Rpc.session.context)[0]
        return name

    def setFieldValid(self, field, value):
        if value:
            if field in self.invalidFields:
                self.invalidFields.remove(field)
        else:
            if not field in self.invalidFields:
                self.invalidFields.append(field)

    def isFieldValid(self, field):
        """
        Checks if the field data is valid

        :param field: field name to check
        :return: True if is valid
        :rtype: bool
        """

        if field in self.invalidFields:
            return False
        else:
            return True

    def setValidate(self):
        change = self.ensureIsLoaded()
        self.invalidFields = []
        for fname in self.group.fieldObjects:
            change = change or not self.isFieldValid(fname)
            self.setFieldValid(fname, True)
        if change:
            self.recordChanged.emit(self)
        return change

    def validate(self):
        """
        Returns True if all fields are valid. Otherwise it returns False.
        :return:
        """
        self.ensureIsLoaded()
        ok = True
        for name in self.group.fieldObjects:
            # The record may not have all the fields the group has.
            # This is because there may have been a switch view to a form
            # but not for this record.
            if not name in self.values:
                continue
            if not self.group.fieldObjects[name].validate(self):
                self.setFieldValid(name, False)
                ok = False
            else:
                self.setFieldValid(name, True)
        return ok

    def context(self):
        """
        Returns the context with which the record has been loaded.
        :return:
        """
        return self.group.context()

    def defaults(self):
        """
        Returns a dict with the default value of each field
        { 'field': defaultValue}
        :return: dict with de default value of each field
        :rtype: dict
        """

        self.ensureIsLoaded()
        value = dict([(name, field.default(self))
                      for name, field in list(self.group.fieldObjects.items())])
        return value

    def setDefaults(self, val):
        """
        Sets the default values for each field from a dict
        { 'field': defaultValue }
        :param val:
        :return:
        """
        self.createMissingFields()
        for fieldname, value in list(val.items()):
            if fieldname not in self.group.fieldObjects:
                continue
            self.group.fieldObjects[fieldname].setDefault(self, value)
        self._loaded = True
        self.recordChanged.emit(self)
        self.recordModified.emit(self)

    def changed(self):
        """
        This functions simply emits a signal indicating that
        the model has changed. This is mainly used by fields
        so they don't have to emit the signal, but relay in
        model emiting it itself.

        :return: None
        :rtype: None
        """

        self.updateAttributes()
        self.recordChanged.emit(self)
        self.recordModified.emit(self)

    def set(self, val, modified=False, signal=True):
        """
        Sets the value on the record

        :param val: Value to set on the Record
        :param modified: True if it's modified from the last value
        :param signal: Enables signal propagation
        :return: None
        :rtype: None
        """

        # Ensure there are values for all fields in the group
        self.createMissingFields()

        later = {}
        for fieldname, value in list(val.items()):
            if fieldname not in self.group.fieldObjects:
                continue
            if isinstance(self.group.fieldObjects[fieldname], ToManyField):
                later[fieldname] = value
                continue
            self.group.fieldObjects[fieldname].set(
                self, value, modified=modified)
        for fieldname, value in list(later.items()):
            self.group.fieldObjects[fieldname].set(
                self, value, modified=modified)

        self.updateAttributes()

        self._loaded = True
        self.modified = modified
        if not self.modified:
            self.modified_fields = {}
        self.recordChanged.emit(self)
        if signal:
            self.recordModified.emit(self)

    def reload(self):
        if not self.id:
            return
        c = Rpc.session.context.copy()
        c.update(self.context())
        if not self.isWizard():
            c['bin_size'] = True
        res = self.rpc.read([self.id], self.group.allFieldNames(), c)
        if res:

            value = res[0]
            self.read_time = time.time()
            # Set signal=False as we don't want the record to be considered
            # modified (as it's not, it's just reloaded).
            self.set(value, signal=False)

    def evaluateExpression(self, dom, checkLoad=True, firstTry=True):
        """
        Evaluates the string expression given by dom. Before passing the dom
        expression to Rpc.session.evaluateExpression a context with
        'current_date', 'time', 'context', 'active_id' and 'parent'
        (if applies) is prepared.

        :param dom:
        :param checkLoad:
        :param firstTry:
        :return:
        """

        if not isinstance(dom, str):
            return dom
        if checkLoad:
            self.ensureIsLoaded()
        d = {}
        for name in self.values:
            d[name] = self.group.fieldObjects[name].get(
                self, checkLoad=checkLoad)

        d['current_date'] = time.strftime('%Y-%m-%d')
        d['time'] = time
        d['context'] = self.context()
        # Avoid setting None in the context as it might be sent to
        # the server and RPC doesn't support None
        d['active_id'] = self.id or False
        # It seems that some modules depend on the existance of 'id'
        # instead of 'active_id'. It has solved, for example, a problem
        # with the c2c_budget module.
        d['id'] = self.id or False
        if self.parent:
            d['parent'] = EvalEnvironment(self.parent)
        try:
            val = Rpc.session.evaluateExpression(dom, d)
        except NameError as exception:
            # If evaluateExpression raises a NameError exception like this one:
            # NameError: name 'unit_amount' is not defined
            # It may be because not all fields are loaded yet, so we'll ensure
            # the model is loaded and re-evaluate. If that doesn't solve the
            # problem (that is firstTry == False) then raise the exception
            # because it's really an issue on the view definition.
            if firstTry:
                self.group.ensureRecordLoaded(self)
                val = self.evaluateExpression(dom, checkLoad, firstTry=False)
            else:
                Debug.error(_('Error evaluating expression: %s') %
                            exception.args)
                val = False
        return val

    def evaluateCondition(self, condition):
        """
        Evaluates the given condition.
        The function will return a boolean, result of applying a condition of
        the form ('field','=','value') or [('field','=','value')]
        :param condition:
        :return:
        """
        # Consider the case when 'condition' is a list
        if isinstance(condition, list):
            result = True
            for c in condition:
                result = result and self.evaluateCondition(c)
            return result

        if not self.fieldExists(condition[0]):
            return False
        value = self.value(condition[0])
        from .Group import RecordGroup
        if isinstance(value, RecordGroup):
            value = value.ids()
        if condition[1] in ('=', '=='):
            if value == condition[2]:
                return True
        elif condition[1] in ('!=', '<>'):
            if value != condition[2]:
                return True
        elif condition[1] == '<':
            if value < condition[2]:
                return True
        elif condition[1] == '>':
            if value > condition[2]:
                return True
        elif condition[1] == '<=':
            if value <= condition[2]:
                return True
        elif condition[1] == '>=':
            if value >= condition[2]:
                return True
        elif condition[1].lower() == 'in':
            for cond in condition[2]:
                if value == cond:
                    return True
        elif condition[1].lower() == 'not in':
            for cond in condition[2]:
                if value == cond:
                    return False
            return True
        return False

    def callOnChange(self, callback):
        """
        This function is called by the field when it's changed and has a
        'on_change' attribute. The 'callback' parameter is the function that
        has to be executed on the server. So the function specified is called
        on the server whenever the field changes.

        :param callback:
        :return:
        """

        match = re.match('^(.*?)\((.*)\)$', callback)
        if not match:
            raise Exception('ERROR: Wrong on_change trigger: %s' % callback)
        func_name = match.group(1)
        arg_names = [n.strip() for n in match.group(2).split(',')]
        args = [self.evaluateExpression(arg) for arg in arg_names]
        ids = self.id and [self.id] or []
        response = getattr(self.rpc, func_name)(ids, *args)
        if response:
            self.set(response.get('value', {}), modified=True)
            if 'domain' in response:
                for fieldname, value in list(response['domain'].items()):
                    if fieldname not in self.group.fieldObjects:
                        continue
                    self.group.fieldObjects[fieldname].attrs['domain'] = value
            warning = response.get('warning', {})
            if warning:
                Notifier.notifyWarning(warning['title'], warning['message'])
            if 'focus' in response:
                self.setFocus.emit(response['focus'])


    def setConditionalDefaults(self, field, value):
        """
        This functions is called whenever a field with 'change_default'
        attribute set to True is modified. The function sets all conditional
        defaults to each field.
        Conditional defaults is a mechanism by which the user can establish
        default values on fields, depending on the value of another field (
        the 'change_default' field). An example of this case is the zip field
        in the partner model.
        :param field:
        :param value:
        :return:
        """
        ir = RpcProxy('ir.values')
        values = ir.get('default', '%s=%s' % (field, value),
                        [(self.group.resource, False)], False, {})
        data = {}
        for index, fname, value in values:
            data[fname] = value
        self.setDefaults(data)

    def isFullyLoaded(self):
        """
        Returns True if the record is loaded and has values for all the fields
        the Group requires.
        :return:
        :rtype: bool
        """
        if not self._loaded:
            return False
        if set(self.values.keys()) == set(self.group.fieldObjects.keys()):
            return True
        else:
            return False

    def isWizard(self):
        """
        Returns True if the Record handles information of a wizard.
        :return:
        """
        return self.group.isWizard()

    def missingFields(self):
        """
        Returns the list of field names the record should have (according to
        group requirements) but it doesn't.
        :return:
        """
        return list(set(self.group.fieldObjects.keys()) - set(self.values.keys()))

    def createMissingFields(self):
        """
        Creates entries in the values dictionary for fields
        returned by missingFields()

        :return:
        """

        # Try to avoid some CPU cycles because this function is called in
        # value() function which will be called lots of times.
        if len(self.group.fieldObjects) == len(self.values):
            return
        for key in self.missingFields():
            val = self.group.fieldObjects[key]
            self.values[key] = val.create(self)
            if (self.new and val.attrs['type'] == 'one2many') and (val.attrs.get('mode', 'tree,form').startswith('form')):
                self.values[key].create()

# vim:noexpandtab:smartindent:tabstop=8:softtabstop=8:shiftwidth=8:
