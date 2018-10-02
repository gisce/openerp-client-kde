#############################################################################
#
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

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Koo.Common import Api
from Koo.Common import Common
from Koo.Plugins import *
from Koo import Rpc

# @brief The Action class is a QAction that can execute a model action. Such
# as relate, print or wizard (on the server) and plugins (on the client).


class Action(QAction):
    def __init__(self, parent):
        """
        Creates a new Action instance given a parent.

        :param parent:
        """
        QAction.__init__(self, parent)
        self._data = None
        self._type = None
        self._model = None

    def setData(self, data):
        """
        Sets the data associated with the action.

        :param data:
        :return:
        """
        self._data = data

    def data(self):
        """
        Returns the data associated with the action.

        :return:
        """
        return self._data

    def setType(self, type):
        """
        Sets the type of action (such as 'print' or 'plugin')

        :param type:
        :return:
        """
        self._type = type

    def type(self):
        """
        Returns the type of action (such as 'print' or 'plugin')
        :return:
        """
        return self._type

    def setModel(self, model):
        """
        Sets the model the action refers to

        :param model:
        :return:
        """
        self._model = model

    def model(self):
        """
        Returns the model the action refers to

        :return:
        """
        return self._model

    def execute(self, currentId, selectedIds, context):
        """
        Executes the action (depending on its type), given the current id and
        the selected ids.

        :param currentId:
        :param selectedIds:
        :param context:
        :return:
        """

        if self._type == 'relate':
            self.executeRelate(currentId, context)
        elif self._type in ('action', 'print'):
            self.executeAction(currentId, selectedIds, context)
        else:
            self.executePlugin(currentId, selectedIds, context)

    def executeRelate(self, currentId, context):
        """
        Executes the action as a 'relate' type

        :param currentId:
        :param context:
        :return:
        """
        if not currentId:
            QMessageBox.information(self, _('Information'), _(
                'You must select a record to use the relate button !'))
        Api.instance.executeAction(self._data, {
            'id': currentId
        }, context)

    def executeAction(self, currentId, selectedIds, context):
        """
        Executes the action as a 'relate' or 'action' type

        :param currentId:
        :param selectedIds:
        :param context:
        :return:
        """
        if not currentId and not selectedIds:
            QMessageBox.information(self, _('Information'), _(
                'You must save this record to use the relate button !'))
            return False

        if not currentId:
            currentId = selectedIds[0]
        elif not selectedIds:
            selectedIds = [currentId]
        if self._type == 'print':
            QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            Api.instance.executeAction(self._data, {
                'id': currentId,
                'ids': selectedIds,
                'model': self._model
            }, context)
        except Rpc.RpcException:
            pass
        if self._type == 'print':
            QApplication.restoreOverrideCursor()

    def executePlugin(self, currentId, selectedIds, context):
        """
        Executes the action as a plugin type

        :param currentId:
        :param selectedIds:
        :param context:
        :return:
        """
        Plugins.execute(self._data, self._model,
                        currentId, selectedIds, context)


class ActionFactory:
    """
    The ActionFactory class is a factory that creates Action objects
    to execute actions on the server. Typically those shown in the toolbar and
    menus for an specific model
    """

    @staticmethod
    def create(parent, definition, model):
        """
        Creates a list of Action objects given a parent, model and definition.

        The 'definition' parameter is the 'toolbar' parameter returned by
        server function fields_view_get.
        :param parent:
        :param definition:
        :param model:
        :return:
        """
        if not definition:
            # If definition is not set we initialize it appropiately
            # to be able to add the 'Print Screen' action.
            definition = {
                'print': [],
                'action': [],
                'relate': []
            }

        # We always add the 'Print Screen' action.
        definition['print'].append({
            'name': 'Print Screen',
            'string': _('Print Screen'),
            'report_name': 'printscreen.list',
            'type': 'ir.actions.report.xml'
        })
        fwidget = parent.parentWidget()
        if not fwidget.isReadonly():
            # Save action
            definition['action'].append({
                'name': 'save',
                'string': _('Save'),
                'shortcut': 'S',
                'action': parent.parentWidget().save,
            })

        # Cancel action
        definition['action'].append({
            'name': 'cancel',
            'string': _('Cancel'),
            'shortcut': 'C',
            'action': parent.parentWidget().cancel,
        })

        actions = []
        for icontype in ('print', 'action', 'relate'):
            for tool in definition[icontype]:
                action = Action(parent)
                action.setIcon(QIcon(":/images/%s.png" % icontype))
                action.setText(Common.normalizeLabel(tool['string']))
                action.setType(icontype)
                action.setData(tool)
                action.setModel(model)

                number = len(actions)

                shortcut = 'Ctrl+'

                # Add save shortcut with Ctrl + S
                if tool['name'] in ["save", "cancel"]:
                    shortcut += tool['shortcut']
                    action.setShortcut(QKeySequence(shortcut))
                    action.setToolTip(action.text() + ' (%s)' % shortcut)
                    action.setIcon(QIcon(":/images/{}.png".format(tool['name'])))
                    action.triggered.connect(tool['action'])

                else:
                    if number > 9:
                        shortcut += 'Shift+'
                        number -= 10
                    if number < 10:
                        shortcut += str(number)
                        action.setShortcut(QKeySequence(shortcut))
                        action.setToolTip(action.text() + ' (%s)' % shortcut)


                actions.append(action)


        plugs = Plugins.list(model)
        for p in sorted(list(plugs.keys()), key=lambda x: plugs[x].get('string', '')):
            action = Action(parent)
            action.setIcon(QIcon(":/images/exec.png"))
            action.setText(str(plugs[p]['string']))
            action.setData(p)
            action.setType('plugin')
            action.setModel(model)
            actions.append(action)
        return actions
