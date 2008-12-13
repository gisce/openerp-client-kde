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

from Koo.FieldWidgets.AbstractFieldWidget import *
from Koo.FieldWidgets.AbstractFieldDelegate import *
from Koo.Common.Numeric import *
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class IntegerFormWidget(AbstractFormWidget):
	def __init__(self, parent, model, attrs={}):
		AbstractFormWidget.__init__(self, parent, model, attrs)
		self.widget = QLineEdit( self )
		layout = QHBoxLayout( self )
		layout.setContentsMargins( 0, 0, 0, 0 )
		layout.addWidget( self.widget )
		self.connect( self.widget, SIGNAL('editingFinished()'), self.calculate )
		self.installPopupMenu( self.widget )

	def calculate(self):
		val = textToInteger( unicode(self.widget.text() ) )
		if val:
			self.widget.setText( str(val) )
		else:
			self.widget.setText('')
		self.modified()

	def value(self):
		return textToInteger( unicode(self.widget.text()) )

	def store(self):
		self.model.setValue(self.name, self.value() )

	def clear(self):
		self.widget.setText('0')

	def showValue(self):
		value = self.model.value( self.name )
		self.widget.setText( str(value) )

	def setReadOnly(self, value):
		self.widget.setEnabled( not value )

	def colorWidget(self):
		return self.widget

class IntegerFieldDelegate( AbstractFieldDelegate ):
	def setModelData(self, editor, model, index):
		value = textToInteger( unicode( editor.text() ) )
		model.setData( index, QVariant( value ), Qt.EditRole )

