##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from Koo.Common.Ui import *

from Koo.Common import Common
from Koo.Common import Shortcuts
from Koo.Fields.AbstractFieldWidget import *

(UrlFieldWidgetUi, UrlFieldWidgetBase) = loadUiType(Common.uiPath('url.ui'))


class UrlFieldWidget(AbstractFieldWidget, UrlFieldWidgetUi):
    def __init__(self, parent, model, attrs={}):
        AbstractFieldWidget.__init__(self, parent, model, attrs)
        UrlFieldWidgetUi.__init__(self)
        self.setupUi(self)

        # Add shortcut
        self.scSearch = QShortcut(self.uiUrl)
        self.scSearch.setKey(Shortcuts.SearchInField)
        self.scSearch.setContext(Qt.WidgetShortcut)
        self.scSearch.activated.connect(self.openUrl)

        self.scClear = QShortcut(self.uiUrl)
        self.scClear.setKey(Shortcuts.ClearInField)
        self.scClear.setContext(Qt.WidgetShortcut)
        self.scClear.activated.connect(self.clear)

        self.uiUrl.setMaxLength(int(attrs.get('size', 16)))
        self.pushOpenUrl.clicked.connect(self.openUrl)
        self.uiUrl.editingFinished.connect(self.modified)
        self.installPopupMenu(self.uiUrl)

    def storeValue(self):
        return self.record.setValue(self.name, str(self.uiUrl.text()) or False)

    def clear(self):
        self.uiUrl.clear()
        self.uiUrl.setToolTip('')

    def showValue(self):
        self.uiUrl.setCursorPosition(0)
        self.uiUrl.setText(self.record.value(self.name) or '')
        self.uiUrl.setToolTip(self.record.value(self.name) or '')

    def setReadOnly(self, value):
        AbstractFieldWidget.setReadOnly(self, value)
        self.uiUrl.setReadOnly(value)

    def openUrl(self):
        value = str(self.uiUrl.text()).strip()
        if value != '':
            Api.instance.createWebWindow(value, value)


class EMailFieldWidget(UrlFieldWidget):
    def openUrl(self):
        value = str(self.uiUrl.text()).strip()
        if value != '':
            QDesktopServices.openUrl(QUrl('mailto:' + value))


class CallToFieldWidget(UrlFieldWidget):
    def openUrl(self):
        value = str(self.uiUrl.text()).strip()
        if value != '':
            QDesktopServices.openUrl(QUrl('callto:%s' + value))


class SipFieldWidget(UrlFieldWidget):
    def openUrl(self):
        value = str(self.uiUrl.text()).strip()
        if value != '':
            QDesktopServices.openUrl(QUrl('sip:%s' + value))

# vim:noexpandtab:
