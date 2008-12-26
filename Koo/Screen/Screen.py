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

import xml.dom.minidom

from Koo.Rpc import RpcProxy
from Koo import Rpc

from Koo.Model.Group import ModelRecordGroup
from Koo.Model.Record import ModelRecord
from Koo.View.ViewFactory import ViewFactory

from Koo.Common import Common
from Koo.Common import Options
from Koo.Common.ViewSettings import *

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import Search
from Koo.Plugins import *
from ToolBar import ToolBar
from Action import *
from ViewQueue import *


## @brief The Screen class is a widget that provides an easy way of handling multiple views.
#
# This class is capable of managing various views of the same model and provides
# functions for moving to the next and previous record.
#
# If neither setViewTypes() nor setViewIds() are called, form and tree views (in this order)
# will be used. If you use only a single 'id' and say it's a 'tree', one you try to switchView
# the default 'form' view will be shown. If you only want to show the 'tree' view, use 
# setViewTypes( [] ) or setViewTypes( ['tree'] )
# When you add a new view by it's ID the type of the given view is removed from the list of
# view types. (See: addViewById() )
#
class Screen(QScrollArea):

	def __init__(self, parent=None):
		QScrollArea.__init__(self, parent)
		self.setFocusPolicy( Qt.NoFocus )

		# GUI Stuff
		self.setFrameShape( QFrame.NoFrame )
		self.setWidgetResizable( True )
		self.container = QWidget( self )
		self.setWidget( self.container )

		self.container.show()

		self.searchForm = Search.SearchFormWidget(self.container)
		self.connect( self.searchForm, SIGNAL('search()'), self.search )
		self.searchForm.hide()
		self.containerView = None

		self.toolBar = ToolBar(self)
		self.toolBar.hide()

		self.layout = QHBoxLayout()
		self.layout.setSpacing( 0 )
		self.layout.setContentsMargins( 0, 0, 0, 0 )
		self.layout.addWidget( self.toolBar )

		vLay = QVBoxLayout( self.container )
		vLay.setContentsMargins( 0, 0, 0, 0 )
		vLay.addWidget( self.searchForm )
		vLay.addLayout( self.layout )

		# Non GUI Stuff
		self.actions = []

		self._embedded = True

		self.views_preload = {}
		self.Rpc = None
		self.name = None
		self.views = []
		self.fields = {}
		self.models = None
		self.__current_model = None

		self.__current_view = 0

		self._viewQueue = ViewQueue()

		self._addAfterNew = False

	def setPreloadedViews(self, views):
		self.views_preload = views

	def preloadedViews(self, views):
		return self.views_preload
		
	def setupViews(self, types, ids):
		self._viewQueue.setup( types, ids )
		# Try to load only if model group has been set
		if self.name:
			self.switchView()

	def setViewIds(self, ids):
		self._viewQueue.setViewIds( ids )
		# Try to load only if model group has been set
		if self.name:
			self.switchView()

	def viewIds(self):
		return self._viewIds

	def setViewTypes(self, types):
		self._viewQueue.setViewTypes( types )
		# Try to load only if model group has been set
		if self.name:
			self.switchView()

	def viewTypes(self):
		return self._viewTypes

	def setAddAfterNew(self, value):
		self._addAfterNew = value

	def addAfterNew(self):
		return self._addAfterNew

	## @brief Sets whether the screen is embedded.
	#
	# Embedded screens don't show the search or toolbar widgets.
	# By default embedded is True so it doesn't load unnecessary forms.
	def setEmbedded(self, value):
		self._embedded = value
		if value:
			self.searchForm.hide()
			self.toolBar.hide()
		else:
			self.searchForm.show()
			self.toolBar.show() 
			if self.currentView() and self.currentView().showsMultipleRecords():
				self.loadSearchForm()

	def embedded(self):
		return self._embedded

	def loadSearchForm(self):
		if self.currentView().showsMultipleRecords() and not self._embedded: 
			if not self.searchForm.isLoaded():
				form = Rpc.session.execute('/object', 'execute', self.resource, 'fields_view_get', False, 'form', self.context)
				self.searchForm.setup( form['arch'], form['fields'], self.resource )

			if self.searchForm.isEmpty():
				self.searchForm.hide()
			else:
				self.searchForm.show()
		else:
			self.searchForm.hide()

	def triggerAction(self):
		if not self.id_get():
			return
		# We expect a Screen.Action here
		action = self.sender()

		id = self.id_get()
		ids = self.selectedIds()

		if action.type() != 'relate':
			self.save()
			self.display()

		action.execute( id, ids )

		if action.type() != 'relate':
			self.reload()

	# Sets the current widget of the Screen
	def setView(self, widget):
		if self.containerView:
			self.disconnect(self.containerView, SIGNAL("activated()"), self.activate )
			self.disconnect(self.containerView, SIGNAL("currentChanged(PyQt_PyObject)"), self.currentChanged)
			self.containerView.hide()

		self.containerView = widget
		# Calling first "loadSearchForm()" because when the search form is hidden
		# it looks better to the user. If we show the widget and then hide the search
		# form it produces an ugly flickering.
		self.loadSearchForm()
		widget.show()
		self.connect(widget, SIGNAL("activated()"), self.activate )
		self.connect(widget, SIGNAL("currentChanged(PyQt_PyObject)"), self.currentChanged)
		

		self.layout.insertWidget( 0, widget )
		self.ensureWidgetVisible( widget )

	def activate( self ):
		self.emit( SIGNAL('activated()') )

	# Searches with the current parameters of the search form and loads the
	# models that fit the criteria.
	def search( self ):
		value = self.searchForm.getValue()
		self.models.setFilter( value )
		self.models.update()

	# Slot to recieve the signal from a view when the current item changes
	def currentChanged(self, model):
		self.setCurrentRecord( model )
		self.emit( SIGNAL('currentChanged()') )

	## @brief Sets the RecordModelGroup this Screen should show.
	# @param models ModelRecordGroup object.
	def setModelGroup(self, modelGroup):
		self.name = modelGroup.resource
		self.resource = modelGroup.resource
		self.context = modelGroup.context
		self.Rpc = RpcProxy(self.resource)

		self.models = modelGroup
		if len(modelGroup.models):
			self.setCurrentRecord( modelGroup.models[0] )
		else:
			self.setCurrentRecord( None )

		modelGroup.addFields(self.fields)
		self.fields.update(modelGroup.fields)

	def currentRecord(self):
		return self.__current_model

	def setCurrentRecord(self, value):
		self.__current_model = value
		try:
			pos = self.models.models.index(value)
		except:
			pos = -1
		if value and value.id:
			id = value.id
		else:
			id = -1
		self.emit(SIGNAL('recordMessage(int,int,int)'), pos, len(self.models.models or []), id)
		if self.__current_model:
			if self.currentView():
				self.currentView().setSelected(self.__current_model.id)

	def switchView(self):
		if self.currentView(): 
			self.currentView().store()

		if self.currentRecord() and ( self.currentRecord() not in self.models.models ):
			self.setCurrentRecord( None )

		if self.loadNextView():
			self.__current_view = len(self.views) - 1
		else:
			self.__current_view = (self.__current_view + 1) % len(self.views)

		self.setView( self.currentView() )
	    	if self.currentRecord():
			self.currentRecord().setValidate()
		self.display()

	## @brief Loads the next view pending to be loaded.
	# If there is no view pending it returns False, otherwise returns True.
	def loadNextView(self):
		if self._viewQueue.isEmpty():
			return False
		if self._viewQueue.isId():
			self.addViewById( self._viewQueue.next() )
		else:
			self.addViewByType( self._viewQueue.next() )
		return True

	def addCustomView(self, arch, fields, display=False, toolbar={}):
		return self.addView(arch, fields, display, True, toolbar=toolbar)

	## @brief Adds a view given its id.
	# @param id View id to load or False if you want to load given view_type.
	# @param display Whether you want the added view to be shown (True) or only loaded (False).
	# @return The view widget
	def addViewById(self, id, display=False):
		# TODO: By now we set toolbar to True always. Even when Screen is embedded
		view = self.Rpc.fields_view_get(id, False, self.context, True)
		return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False), id=id)
		
	## @brief Adds a view given a view type.
	# @param type View type ('form', 'tree', 'calendar', 'graph'...). 
	# @param display Whether you want the added view to be shown (True) or only loaded (False).
	# @return The view widget
	def addViewByType(self, type, display=False):
		if type in self.views_preload:
			return self.addView(self.views_preload[type]['arch'], self.views_preload[type]['fields'], display, toolbar=self.views_preload[type].get('toolbar', False), id=self.views_preload[type].get('view_id',False))
		else:
			# TODO: By now we set toolbar to True always. Even when the Screen is embedded
			view = self.Rpc.fields_view_get(False, type, self.context, True)
			return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False), id=view['view_id'])
		
	## @brief Adds a view given it's XML description and fields
	# @param arch XML string: typically 'arch' field returned by model fields_view_get() function.
	# @param fields Fields dictionary containing each field (widget) properties.
	# @param display Whether you want the added view to be shown (True) or only loaded (False)
	# @param custom If True, fields are added to those existing in the model
	# @param id View id. This parameter is used for storing and loading settings for the view. If id=False, no
	#		settings will be stored/loaded.
	# @return The view widget
	def addView(self, arch, fields, display=False, custom=False, toolbar={}, id=False):
		def _parse_fields(node, fields):
			if node.nodeType == node.ELEMENT_NODE:
				if node.localName=='field':
					attrs = Common.nodeAttributes(node)
					if attrs.get('widget', False):
						if attrs['widget']=='one2many_list':
							attrs['widget']='one2many'
						attrs['type'] = attrs['widget']
					try:
						fields[attrs['name']].update(attrs)
					except:
						print "-"*30,"\n malformed tag for :", attrs
						print "-"*30
						raise						
			for node2 in node.childNodes:
				_parse_fields(node2, fields)
		dom = xml.dom.minidom.parseString(arch.encode('utf-8'))
		_parse_fields(dom, fields)

		models = self.models.models
		if self.currentRecord() and (self.currentRecord() not in models):
			models = models + [self.currentRecord()]
		if custom:
			self.models.addCustomFields(fields)
		else:
			self.models.addFields(fields)

		self.fields = self.models.fields

		dom = xml.dom.minidom.parseString(arch.encode('utf-8'))
		view, on_write = ViewFactory.create(self, self.resource, dom, self.fields)
		self.setOnWrite( on_write )
		view.id = id
		# Load view settings
		view.setViewSettings( ViewSettings.load( view.id ) )

		self.views.append(view)
		self.loadActions( toolbar )

		if display:
			self.__current_view = len(self.views) - 1
			self.currentView().display(self.currentRecord(), self.models)
			self.setView(view)
		return view

	def loadActions( self, actions ):
		self.actions = ActionFactory.create( self, actions, self.resource )
		if self.actions:
			for action in self.actions:
				self.connect( action, SIGNAL('triggered()'), self.triggerAction )
			# If there's only one action it will be the 'Print Screen' action
			# that is added "manually" by ActionFactory. In those cases in which
			# Print Screen is the only action we won't show it in the toolbar. We
			# don't consider Plugins a good reason to show the toolbar either.
			# This way dashboards won't show the toolbar, though the option will
			# remain available in the menu for those screens that don't have any
			# actions configured in the server, but Print Screen can be useful.
			if len(self.actions) > 1 + len(Plugins.list()) and Options.options['show_toolbar']:
				self.toolBar.setup( self.actions )

	def isReadOnly(self):
		return self.currentView().isReadOnly()

	def new(self, default=True):
		if self.currentView() and self.currentView().showsMultipleRecords() \
				and self.currentView().isReadOnly():
			self.switchView()
		model = self.models.newModel(default, self.models.domain(), self.context)

		if (not self.currentView() ) or self.currentView().model_add_new or self._addAfterNew:
			self.models.addModel(model, self.new_model_position())

		if self.currentView():
			self.currentView().reset()

		self.setCurrentRecord( model )
		self.display()
		return self.currentRecord()

	def new_model_position(self):
		position = -1
		if self.currentView() and self.currentView().showsMultipleRecords() \
			    and self.currentView().isReadOnly():
			#and self.currentView().editable == 'top':
			position = 0
		return position

	def setOnWrite(self, func_name):
		self.models.on_write = func_name

	def cancel_current(self):
		if not self.currentRecord():
			return
		self.currentRecord().cancel()

	def save(self):
 		if not self.currentRecord():
 			return False
 		self.currentView().store()
		
		id = False
		if self.currentRecord().validate():
			id = self.currentRecord().save(reload=True)
		else:
			self.currentView().display(self.currentRecord(), self.models)
			return False
		
		if self.currentView().showsMultipleRecords():
			for model in self.models.models:
				if model.isModified():
					if model.validate():
						id = model.save(reload=True)
					else:
						self.setCurrentRecord( model )
						self.display()
						return False
			self.display()

		if not self.models.modelExists( self.currentRecord() ):
			self.models.addModel( self.currentRecord() )
		self.display()
		return id

	def reload(self):
		if self.currentView().showsMultipleRecords():
                        id = self.id_get()
                        ids = self.ids_get()
                        self.clear()
                        self.load(ids)
                        for model in self.models:
                                if model.id == id:
                                        self.setCurrentRecord( model )
                                        self.display()
                                        break	
                else:
                        self.cancel_current()
                        self.display()

	def currentView(self):
		if not len(self.views):
			return None
		return self.views[self.__current_view]

	def get(self):
		if not self.currentRecord():
			return None
		self.currentView().store()
		return self.currentRecord().get()

	def isModified(self):
		if not self.currentRecord():
			return False
		self.currentView().store()
		res = False
		if self.currentView().view_type.showsMultipleRecords():
			for model in self.models.models:
				if model.isModified():
					res = True
		else:
			res = self.currentRecord().isModified()
		return res 

	def reload(self):		
		self.currentRecord().reload()
		self.display()

	def remove(self, unlink = False):
		ids = self.selectedIds()
		if unlink and ids:
			# Remove records with id None as they would cause an exception
			# trying to remove from the server 
			idsToUnlink = [x for x in ids if x != None]
			unlinked = self.Rpc.unlink( idsToUnlink )	
			# Try to be consistent with database
			# If records could not be removed from the database
			# don't remove them on the client. Don't report it directly
			# though as probably an exception (Warning) has already
			# been shown to the user.
			if not unlinked:
				return False
		for x in ids:
			model = self.models[x]
			idx = self.models.models.index(model)
			self.models.remove( model )
			if self.models.models:
				idx = min(idx, len(self.models.models)-1)
				self.setCurrentRecord( self.models.models[idx] )
			else:
				self.setCurrentRecord( None )
		self.display()
		if ids:
			return True
		else:
			return False

	def load(self, ids):
		self.currentView().reset()
		self.models.load( ids, display =True )
		if ids:
			self.display(ids[0])
		else:
			self.setCurrentRecord( None )
			self.display()

	def display(self, res_id=None):
		if res_id:
			self.setCurrentRecord( self.models[res_id] )
		if self.views:
			self.currentView().display(self.currentRecord(), self.models)

	def display_next(self):
		self.currentView().store()
		if self.currentRecord() in self.models.models:
			idx = self.models.models.index(self.currentRecord())
			idx = (idx+1) % len(self.models.models)
			self.setCurrentRecord( self.models.models[idx] )
		else:
			self.setCurrentRecord( len(self.models.models) and self.models.models[0] )
		if self.currentRecord():
			self.currentRecord().setValidate()
		self.display()

	def display_prev(self):
		self.currentView().store()
		if self.currentRecord() in self.models.models:
			idx = self.models.models.index(self.currentRecord())-1
			if idx<0:
				idx = len(self.models.models)-1
			self.setCurrentRecord( self.models.models[idx] )
		else:
			self.setCurrentRecord( len(self.models.models) and self.models.models[-1] )

		if self.currentRecord():
			self.currentRecord().setValidate()
		self.display()

	def selectedIds(self):
		return self.currentView().selectedIds()

	def id_get(self):
		if self.currentRecord():
			return self.currentRecord().id
		else:
			return None

	def ids_get(self):
		return [x.id for x in self.models if x.id]

	def clear(self):
		self.models.clear()
		self.display()

	# Stores settings of all opened views
	def storeViewSettings(self):
		for view in self.views:
			ViewSettings.store( view.id, view.viewSettings() )

# vim:noexpandtab:
