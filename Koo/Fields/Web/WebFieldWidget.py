##############################################################################
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

from PyQt5.QtNetwork import *
from Koo.Fields.AbstractFieldWidget import *

(WebFieldWidgetUi, WebFieldWidgetBase) = loadUiType(Common.uiPath('web.ui'))


class CookieJar(QNetworkCookieJar):
    """
    The CookieJar class inherits QNetworkCookieJar to make a couple of
    functions public.
    """
    def __init__(self, parent=None):
        QNetworkCookieJar.__init__(self, parent)

    def allCookies(self):
        return QNetworkCookieJar.allCookies(self)

    def setAllCookies(self, cookieList):
        QNetworkCookieJar.setAllCookies(self, cookieList)


class WebFieldWidget(AbstractFieldWidget, WebFieldWidgetUi):
    def __init__(self, parent, model, attrs=None):
        if attrs is None:
            attrs = {}
        AbstractFieldWidget.__init__(self, parent, model, attrs)
        WebFieldWidgetUi.__init__(self)
        self.setupUi(self)

    def sizeHint(self):
        size = super(WebFieldWidget, self).sizeHint()
        width = self.attrs.get('width')
        height = self.attrs.get('height')
        if width:
            size.setWidth(int(width))
        if height:
            size.setHeight(int(height))
        return size

    def storeValue(self):
        pass

    def clear(self):
        self.uiWeb.setUrl(QUrl(''))

    def showValue(self):
        value = self.record.value(self.name) or ''
        url = QUrl(value)
        if not value or str(url.scheme()):
            self.uiWeb.setUrl(url)
        else:
            self.uiWeb.setHtml(value)

    def setReadOnly(self, value):
        AbstractFieldWidget.setReadOnly(self, value)
        # We always enable the browser so the user can use links.
        self.uiWeb.setEnabled(True)
