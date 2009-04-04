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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.uic import *
from PyQt4.QtWebKit import *
from Koo.Common import Common
from Koo.Fields.AbstractFieldWidget import *

(WebFieldWidgetUi, WebFieldWidgetBase) = loadUiType( Common.uiPath('web.ui') ) 

class WebFieldWidget(AbstractFieldWidget, WebFieldWidgetUi):
	def __init__(self, parent, model, attrs={}):
		AbstractFieldWidget.__init__(self, parent, model, attrs)
		WebFieldWidgetUi.__init__(self)
		self.setupUi( self )

	def store(self):
		pass

	def clear( self ):
		self.uiWeb.setUrl(QUrl(''))

	def showValue(self):
		self.uiWeb.setUrl(QUrl(self.record.value(self.name) or ''))

	def setReadOnly(self, value):
		# We always enable the browser so the user can use links.
		self.uiWeb.setEnabled( True )

# vim:noexpandtab:

