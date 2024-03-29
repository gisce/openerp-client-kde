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
from PyQt5.QtWidgets import *

from Koo.Rpc import RpcProxy
from Koo import Rpc

from Koo.Model.Group import RecordGroup
from Koo.Model.Record import Record
from Koo.View.ViewFactory import ViewFactory

from Koo.Common import Common
from Koo.Common.Settings import *
from Koo.Common.ViewSettings import *

from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Koo.Search import SearchFormWidget
from Koo.Plugins import *
from .ToolBar import ToolBar
from .Action import *
from .ViewQueue import *


class Screen(QScrollArea):
    """
    The Screen class is a widget that provides an easy way of handling
    multiple views.

    This class is capable of managing various views of the same model and
    provides functions for moving to the next and previous record.

    If neither setViewTypes() nor setViewIds() are called, form and tree views
    (in this order) will be used. If you use only a single 'id' and say it's a
    'tree', one you try to switchView the default 'form' view will be shown. If
    you only want to show the 'tree' view, use setViewTypes( [] ) or
    setViewTypes( ['tree'] )

    When you add a new view by it's ID the type of the given view is removed
    from the list of view types. (See: addViewById() )

    A Screen can emit four different signals:
        activated() -> Emited each time a record is activated (such as a
        double click on a list).
        closed() -> Emited when a view asks for the screen to be closed (such
        as a 'close' button on a form).
        currentChanged() -> Emited when the current record has been modified.
        recordMessage(int,int,int) -> Emited each time the current record
        changes (such as moving to previous or next).
    """
    activated = pyqtSignal()
    closed = pyqtSignal()
    currentChangedSignal = pyqtSignal()
    recordMessage = pyqtSignal(int, int, int)
    statusMessage = pyqtSignal('QString')

    def __init__(self, parent=None):
        QScrollArea.__init__(self, parent)
        self.setFocusPolicy(Qt.NoFocus)

        # GUI Stuff
        self.setFrameShape(QFrame.NoFrame)
        self.setWidgetResizable(True)
        self.container = QWidget(self)
        self.setWidget(self.container)

        self.container.show()

        self.searchForm = SearchFormWidget(self.container)
        # @xtorello toreview
        self.searchForm.performSearch.connect(self.search)
        self.searchForm.keyDownPressed.connect(self.setFocusToView)
        self.searchForm.hide()
        self.containerView = None

        self.toolBar = ToolBar(self)
        self.setToolbarVisible(False)

        self.viewLayout = QVBoxLayout()

        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.viewLayout)
        self.layout.addWidget(self.toolBar)

        vLay = QVBoxLayout(self.container)
        vLay.setContentsMargins(0, 0, 0, 0)
        vLay.addWidget(self.searchForm)
        vLay.addLayout(self.layout)

        # Non GUI Stuff
        self.actions = []

        self._embedded = True

        self.views_preload = {}
        self.rpc = None
        self.name = None
        self.views = {}
        self.fields = {}
        self.group = None
        self._currentRecordPosition = None
        self._currentRecord = None
        self._currentView = -1
        self._previousView = -1

        self._viewQueue = ViewQueue()
        self._readOnly = False
        # The first time Screen is shown it will try to setCurrentRecord
        # if none is selected.
        self._firstTimeShown = True

        # @xtorello toreview signal to method integration
        self.currentChangedSignal.connect(self.currentChanged)

    def save(self):
        """
        Dummy save
        :return: None
        :rtype: None
        """
        pass

    def cancel(self):
        """
        Dummy cancel
        :return: None
        :rtype: No
        """
        pass

    def showEvent(self, event):
        if self._firstTimeShown:
            self._firstTimeShown = False
            # The first time Screen is shown/rendered we'll set current record
            # if none is yet selected. Note that this means that it's not
            # possible to explicitly make Screen NOT select any items.
            #
            # The reason for doing this is that it allows delayed loading of
            # embedded one2many and many2many fields because those not in the
            # main tab won't receive the 'showEvent' and won't try to load data
            # from the server, which greatly improves load time of some forms.
            #
            # If we don't do this here, and let 2many widgets to try to
            # implement it, they have to set current record on switchView, but
            # the problem is that label is kept as 0/0 (instead of 1/3, for
            # example), until user clicks switch view.
            if self.group and self.group.count() and not self.currentRecord():
                self.setCurrentRecord(self.group.recordByIndex(0))
        return QScrollArea.showEvent(self, event)

    def setFocusToView(self):
        """
        Sets the focus to current view.
        :return:
        """
        self.currentView().setFocus()

    def sizeHint(self):
        return self.container.sizeHint()

    def setPreloadedViews(self, views):
        self.views_preload = views

    def preloadedViews(self, views):
        return self.views_preload

    def setupViews(self, types, ids):
        """
        Initializes the list of views using a types list and an ids list.

        Example:

        screen.setupViews( ['tree','form'], [False, False] )
        :param types:
        :param ids:
        :return: None
        :rtype: None
        """
        self._viewQueue.setup(types, ids)
        # Try to load only if model group has been set
        if self.name:
            self.switchView()

    def setViewIds(self, ids):
        self._viewQueue.setViewIds(ids)
        # Try to load only if model group has been set
        if self.name:
            self.switchView()

    def viewIds(self):
        return self._viewIds

    def setViewTypes(self, types):
        self._viewQueue.setViewTypes(types)
        # Try to load only if model group has been set
        if self.name:
            self.switchView()


    def setEmbedded(self, value):
        """
        Sets whether the screen is embedded.

        Embedded screens don't show the search or toolbar widgets.
        By default embedded is True so it doesn't load unnecessary forms.
        :param value:
        :return:
        """
        self._embedded = value
        self.setToolbarVisible(not value)
        self.setSearchFormVisible(not value)

    def embedded(self):
        """
        Returns True if the Screen acts in embedded mode.
        :return:
        """
        return self._embedded

    # @brief
    def setToolbarVisible(self, value):
        """
        Allows making the toolbar visible or hidden.
        :param value:
        :return:
        """
        self._toolbarVisible = value
        self.toolBar.setVisible(value)

    # @brief Allows making the search form visible or hidden.
    def setSearchFormVisible(self, value):
        self._searchFormVisible = value
        self.searchForm.setVisible(value)
        if value:
            if self.currentView() and self.currentView().showsMultipleRecords():
                self.loadSearchForm()

    def loadSearchForm(self):
        if not Settings.value('koo.show_search_form', True):
            self.searchForm.hide()
            return
        if self.currentView().showsMultipleRecords() and not self._embedded:
            if not self.searchForm.isLoaded():
                form = Rpc.session.execute(
                    '/object', 'execute', self.resource, 'fields_view_get', False, 'form', self.context)
                tree = Rpc.session.execute(
                    '/object', 'execute', self.resource, 'fields_view_get', False, 'tree', self.context)
                fields = form['fields']
                fields.update(tree['fields'])
                arch = form['arch']

                # Due to the fact that searchForm.setup() requires an XML and we want it to
                # be able to process select=True from both form and tree, we need to fake
                # an XML.

                dom = xml.dom.minidom.parseString(tree['arch'].encode('utf-8'))
                children = dom.childNodes[0].childNodes
                tempArch = ''
                for i in range(1, len(children)):
                    tempArch += children[i].toxml()
                # Generic case when we need to remove the last occurance of </form> from form view
                arch = arch[0:form['arch'].rfind('</form>')]
                # Special case when form is replaced,we need to remove </form>
                index = arch.rfind('</form>')
                if index > 0:
                    arch = arch[0:index]
                arch = arch + tempArch + '\n</form>'

                self.searchForm.setup(
                    arch, fields, self.resource, self.group.domain())

            self.searchForm.show()
        else:
            self.searchForm.hide()

    def setReadOnly(self, value):
        self._readOnly = value
        self.display()

    def isReadOnly(self):
        return self._readOnly

    def triggerAction(self):
        """
        This function is expected to be used as a slot for an Action trigger
        signal.
        (as it will check the sender). It will call the Action.execute(id,ids)
        function.
        :return:
        """
        # We expect a Screen.Action here
        action = self.sender()

        # If record has been modified save before executing the action.
        # Otherwise:
        # - With new records nothing is done without notifying the user
        # which isn't intuitive.
        # - With existing records it prints (for example) old values, which
        # isn't intuitive either.
        if self.isModified():
            if not self.save():
                return

        # Do not trigger action if there is no record selected. This is
        # only permitted for plugins.
        if not self.currentId() and action.type() != 'plugin':
            return

        ident = self.currentId()
        ids = self.selectedIds()

        if action.type() != 'relate':
            self.save()
            self.display()

        context = self.context.copy()
        if self.currentRecord():
            # Plugins may be executed even if there's no current record.
            context.update(self.currentRecord().get())

        action.execute(ident, ids, context)

        if action.type() != 'relate':
            self.reload()

    # @brief Sets the current widget of the Screen
    def setView(self, widget):
        if self.containerView:
            self.containerView.activated.disconnect(self.activate)
            self.containerView.currentChanged['PyQt_PyObject'].disconnect(self.currentChanged)
            self.containerView.statusMessage['QString'].disconnect(self.statusMessage['QString'])
            self.containerView.hide()

        self.containerView = widget
        # Calling first "loadSearchForm()" because when the search form is
        # hidden
        # it looks better to the user. If we show the widget and then hide the
        # search form it produces an ugly flickering.
        self.loadSearchForm()
        self.containerView.show()
        # @xtorello toreview zzz
        widget.activated.connect(self.activate)
        widget.currentChanged['PyQt_PyObject'].connect(self.currentChanged)
        widget.statusMessage['QString'].connect(self.statusMessage['QString'])

        # Set focus proxy so other widgets can try to setFocus to us
        # and the focus is set to the expected widget.
        self.setFocusProxy(self.containerView)

        self.ensureWidgetVisible(widget)
        self.updateGeometry()

    def activate(self):
        self.activated.emit()

    def close(self):
        # @xtorello @xbarnada TODO revisar si hi ha canvis pendents d'aplicar abans de tancar
        ## veure FormWidget.canClose / modifiedSave
        self.closed.emit()

    def search(self):
        """
        Searches with the current parameters of the search form and loads the
        models that fit the criteria.
        :return:
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            value = self.searchForm.value()
            self.group.setFilter(value)
            # We setCurrentRecord( None ) first because self.group.update()
            # can emit some events that can be used to query the currentRecord().
            # Previous record may not exist and cause an exception.
            self.setCurrentRecord(None)
            self.group.update()
            if self.group.count() > 0:
                self.setCurrentRecord(self.group.recordByIndex(0))
            else:
                self.setCurrentRecord(None)
            self.display()
        except Rpc.RpcException as e:
            pass
        QApplication.restoreOverrideCursor()

    def updateSearchFormStatus(self):
        # Do not allow searches if group is modified. This avoids 'maximum recursion' errors if user
        # tries to search after modifying a record in an editable list.
        if self.group.isModified():
            self.searchForm.setEnabled(False)
        else:
            self.searchForm.setEnabled(True)

    # Slot to recieve the signal from a view when the current item changes
    @pyqtSlot()
    def currentChanged(self, model):
        self.setCurrentRecord(model)
        self.currentChanged.emit()
        self.updateSearchFormStatus()

    def setRecordGroup(self, group):
        """
        @brief Sets the RecordGroup this Screen should show.

        :param group: group RecordGroup object
        :return: None
        :rtype: None
        """
        if not group:
            self.group = None
            self._currentRecord = None
            self._currentRecordPosition = None
            # Call setCurrentRecord() after setting self.group
            # because it will emit a signal with the count of elements
            # which must be 0.
            self.setCurrentRecord(None)
            return

        self.name = group.resource
        self.resource = group.resource
        self.context = group.context()
        self.rpc = RpcProxy(self.resource)

        self.group = group
        self._currentRecord = None
        self._currentRecordPosition = None

        group.addFields(self.fields)
        self.fields.update(group.fields)

        if self.isVisible():
            if self.group and self.group.count() and not self.currentRecord():
                self.setCurrentRecord(self.group.recordByIndex(0))
            else:
                # Note that we need to setCurrentRecord so it is initialized and
                # emits the recordMessage() signal.
                self.setCurrentRecord(None)

            self._firstTimeShown = False
        else:
            self._firstTimeShown = True

    def currentRecord(self):
        """
        Returns a reference the current record (Record).
        :return:
        """

        # Checking _currentRecordPosition before count() can save a search()
        # call to the server because count() will execute a search() in the
        # server if no items have been loaded yet. What happens is that the
        # first time a screen with a TreeView is shown currentRecord() will be
        # called but there will be no currentRecord. TreeView then will set the
        # appropiate order by loading settings from the server through
        # restoreViewSettings, and KooModel will load data on demand.
        if self._currentRecordPosition and self._currentRecordPosition >= 0 and self.group.count():
            # In some cases self._currentRecordPosition might point to a
            # position beyond group size. In this case ensure current record
            # is set to None.
            if self._currentRecordPosition >= self.group.count():
                self.setCurrentRecord(None)
                return None
            # Use modelByIndex because this ensures all missing fields of the
            # model are loaded. For example, the model could have been loaded
            # in tree view but now might need more fields for form view.
            return self.group.modelByIndex(self._currentRecordPosition)
        else:
            # New records won't have that problem (althouth the problem might
            # be that fields haven't been created yet??)
            return self._currentRecord

    def setCurrentRecord(self, value):
        """
        Sets the current record.

        Note that value will be a reference to the Record.
        :param value:
        :return:
        """

        if self.group and self.group.recordExists(value):
            pos = self.group.indexOfRecord(value)
        else:
            pos = -1
        # In order to "discover" if we need to update current record we
        # use "self._currentRecordPosition", because setRecordGroup sets
        # self._currentRecordPosition = None and then calls
        # setCurrentRecord( None )
        # Which will make pos = -1 and will emit the recordMessage() signal.
        #
        # Trying to "discover" this with self._currentRecord will not work.
        if self._currentRecordPosition == pos:
            return
        self._currentRecord = value
        self._currentRecordPosition = pos
        if value and value.id:
            ident = value.id
        else:
            ident = -1
        if self.group:
            count = self.group.count()
        else:
            count = 0
        self.recordMessage.emit(pos, count, ident)
        if self._currentRecord:
            if self.currentView():
                self.currentView().setSelected(self._currentRecord)

    def switchView(self, viewType=None):
        """
        Switches the current view to the previous one. If viewType
        (such as 'calendar') is given it will switch to that view type.
        :param viewType:
        :return:
        """

        if self.currentView():
            self.currentView().store()

        if self.currentRecord() and (not self.group.recordExists(self.currentRecord())):
            self.setCurrentRecord(None)

        if viewType:
            self._previousView = self._currentView
            self._currentView = self._viewQueue.indexFromType(viewType)
        else:
            if self._currentView >= 0:
                # Swap currentView and previousView values
                self._currentView, self._previousView = self._previousView, self._currentView
            else:
                self._currentView = 0
            # The second time switchView is executed, currentView might get -1
            # and we want it in fact to be 1 ...
            self._currentView = abs(self._currentView)
            # ... unless there's only one view
            self._currentView = min(
                self._currentView, self._viewQueue.count() - 1)

        # If the view can show multiple records we set the default loading
        # method in the record group, otherwise we set the load one-by-one
        # mode, so only the current record is loaded. This improves performance
        # on switching views from list to form with forms that contain a lot
        # of fields.

        if self.currentView().showsMultipleRecords():
            self.group.setLoadOneByOne(False)
        else:
            self.group.setLoadOneByOne(True)

        self.setView(self.currentView())
        if self.currentRecord():
            self.currentRecord().setValidate()
        self.display()

    def addViewByIdAndType(self, id, type, display=False):
        """
        Adds a view given it's id and type.

        This function is needed to resemble server's fields_view_get function.
        This function wasn't necessary but accounting module needs it because
        it tries to open a view with it's ID but reimplements fields_view_get
        and checks the view type.

        see AddViewById
        see AddViewByType
        :param id:
        :param type:
        :param display:
        :return:
        """
        if type in self.views_preload:
            return self.addView(
                self.views_preload[type]['arch'],
                self.views_preload[type]['fields'], display,
                toolbar=self.views_preload[type].get('toolbar', False),
                ident=self.views_preload[type].get('view_id', False)
            )
        else:
            # By now we set toolbar to True always. Even when the Screen is
            # embedded.
            # This way we don't force setting the embedded option in the
            # class constructor and can be set later.
            view = self.rpc.fields_view_get(id, type, self.context, True)
            return self.addView(
                view['arch'], view['fields'], display,
                toolbar=view.get('toolbar', False),
                ident=view.get('view_id', False)
            )

    def addViewById(self, id, display=False):
        """
        Adds a view given its id.

        see AddViewByType
        seee AddViewByIdAndType
        :param id: View id to load or False if you want to load given view_type.
        :param display: Whether you want the added view to be shown (True) or
        only loaded (False).
        :return: The view widget
        """
        # By now we set toolbar to True always. Even when the Screen is embedded.
        # This way we don't force setting the embedded option in the class constructor
        # and can be set later.
        view = self.rpc.fields_view_get(id, False, self.context, True)
        return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False), id=id)

    def addViewByType(self, type, display=False):
        """
        see AddViewById
        see AddViewByIdAndType
        :param type: View type ('form', 'tree', 'calendar', 'graph'...).
        :param display: Whether you want the added view to be shown (True) or
        only loaded (False).
        :return: The view widget
        """
        if type in self.views_preload:
            return self.addView(self.views_preload[type]['arch'], self.views_preload[type]['fields'], display, toolbar=self.views_preload[type].get('toolbar', False), id=self.views_preload[type].get('view_id', False))
        else:
            # By now we set toolbar to True always. Even when the Screen is embedded.
            # This way we don't force setting the embedded option in the class constructor
            # and can be set later.
            view = self.rpc.fields_view_get(False, type, self.context, True)
            return self.addView(view['arch'], view['fields'], display, toolbar=view.get('toolbar', False), ident=view.get('view_id', False))

    def _parse_fields(self, node, fields):
        if node.nodeType == node.ELEMENT_NODE:
            if node.localName == 'field':
                attrs = Common.nodeAttributes(node)
                if attrs.get('widget', False):
                    if attrs['widget'] == 'one2many_list':
                        attrs['widget'] = 'one2many'
                    attrs['type'] = attrs['widget']
                try:
                    fields[attrs['name']].update(attrs)
                except:
                    print("-" * 30, "\n malformed tag for :", attrs)
                    print("-" * 30)
                    raise
        for node2 in node.childNodes:
            self._parse_fields(node2, fields)

    def addView(self, arch, fields, display=False, toolbar=None, ident=False):
        """
        Adds a view given it's XML description and fields

        :param arch: typically 'arch' field returned by model fields_view_get()
        function.
        :type arch: str
        :param fields: Fields dictionary containing each field (widget)
        properties.
        :param display: Whether you want the added view to be shown (True) or
        only loaded (False)
        :param toolbar: Toolbar information as returned from fields_view_get
        server function.
        :param ident: View id. This parameter is used for storing and loading
        settings for the view. If id=False, no
        :return: The view widget
        """
        if toolbar is None:
            toolbar = {}

        dom = xml.dom.minidom.parseString(arch.encode('utf-8'))
        self._parse_fields(dom, fields)

        self.group.addFields(fields)

        self.fields = self.group.fields

        view = ViewFactory.create(ident, self, self.resource, dom, self.fields)
        self.viewLayout.addWidget(view)
        self.setOnWriteFunction(view.onWriteFunction())
        # Load view settings
        if not self.group.updated:
            domain = self.group.domain()
            self.group.setDomainForEmptyGroup()
            view.setViewSettings(ViewSettings.load(view.id))
            self.group.setDomain(domain)
        else:
            view.setViewSettings(ViewSettings.load(view.id))

        self.views[view.viewType()] = view
        self.loadActions(toolbar)

        if display:
            if not self._viewQueue.typeExists(view.viewType()):
                self._viewQueue.addViewType(view.viewType())
            self._currentView = self._viewQueue.indexFromType(view.viewType())
            self.currentView().display(self.currentRecord(), self.group)
            self.setView(view)
        return view

    def loadActions(self, actions):
        """
        Loads all actions associated with the current model including plugins.
        :param actions:
        :return:
        """
        self.actions = ActionFactory.create(self, actions, self.resource)
        if self.actions:
            for action in self.actions:
                action.triggered.connect(self.triggerAction)
            # If there's only one action it will be the 'Print Screen' action
            # that is added "manually" by ActionFactory. In those cases in which
            # Print Screen is the only action we won't show it in the toolbar.
            # We don't consider Plugins a good reason to show the toolbar
            # either.
            # This way dashboards won't show the toolbar, though the option will
            # remain available in the menu for those screens that don't have any
            # actions configured in the server, but Print Screen can be useful.
            if len(self.actions) > 0 and Settings.value('koo.show_toolbar') and self._toolbarVisible:
                self.toolBar.setup(self.actions)
                self.toolBar.show()
            else:
                self.toolBar.hide()

    def new(self, default=True, context=None):
        """
        Creates a new record in the current model. If the current view is not editable
        it will automatically switch to a view that allows editing.
        :param default:
        :param context:
        :return:
        """
        if context is None:
            context = {}

        if self.currentView() and self.currentView().showsMultipleRecords() \
                and self.currentView().isReadOnly():
            self.switchView('form')

        ctx = self.context.copy()
        ctx.update(context)
        record = self.group.create(
            default, self.newRecordPosition(), self.group.domain(), ctx)

        if self.currentView():
            self.currentView().reset()

        self.setCurrentRecord(record)
        self.display()

        if self.currentView():
            self.currentView().startEditing()
        return self.currentRecord()

    def newRecordPosition(self):
        """
        Returns 0 or -1 depending on new records policy for the
        current view.
        If the view adds on top it will return 0, otherwise it will return -1
        :return:
        :rtype: int
        """
        if self.currentView() and self.currentView().addOnTop():
            return 0
        else:
            return -1

    def addOnTop(self):
        """
        Returns whether new records will be added on top or on the bottom.

        Note that this is a property defined by the current view. If there's
        no current view it will return False.
        :return:
        """
        if self.currentView():
            return self.currentView().addOnTop()
        else:
            return False

    def setOnWriteFunction(self, functionName):
        """
        Sets the on_write function. That is the function (in the server) that
        must be called after storing a record.
        :param functionName:
        :return:
        """
        self.group.setOnWriteFunction(functionName)

    def save(self):
        """
        Stores all modified models.
        :return:
        """
        if not self.currentRecord():
            return False
        self.currentView().store()

        ident = False
        if self.currentRecord().validate():
            ident = self.currentRecord().save(reload=True)
        else:
            self.currentView().display(self.currentRecord(), self.group)
            return False

        if self.currentView().showsMultipleRecords():
            for record in self.group.modifiedRecords():
                if record.validate():
                    ident = record.save(reload=True)
                else:
                    self.setCurrentRecord(record)
                    self.display()
                    return False
            self.display()

        self.display()
        return ident

    # @brief Reload current model and refreshes the view.
    #
    # If the current view only shows a single record, only the current one will
    # be reloaded. If the view shows multiple records it will reload the whole model.
    def reload(self):
        if not self.currentView().showsMultipleRecords():
            if self.currentRecord():
                self.currentRecord().reload()
                self.display()
            return

        id = 0
        idx = -1
        if self.currentRecord():
            id = self.currentId()
            idx = self.group.indexOfRecord(self.currentRecord())

        # If we didn't cancel before updating, update may not work if there were modified
        # records. So we first ensure the group is not set as modified and then update/reload
        # it. Note that not cancelling here has other side effects such as that group.sortAll
        # may send a "could not sort" signal and cause an infinite recursion exception.
        self.cancel()
        self.group.update()
        if id:
            record = self.group.modelById(id)

            if record:
                self.setCurrentRecord(record)
            else:
                # If what it was the current record no longer exists
                # at least keep index position
                idx = min(idx, self.group.count() - 1)
                if idx >= 0:
                    self.setCurrentRecord(self.group.recordByIndex(idx))
                else:
                    self.setCurrentRecord(None)
        else:
            self.setCurrentRecord(None)
        self.display()

    # @brief Removes all new records and marks all modified ones as not loaded.
    def cancel(self):
        idx = -1
        if self.currentRecord():
            idx = self.group.indexOfRecord(self.currentRecord())

        self.group.cancel()
        if idx != -1:
            idx = min(idx, self.group.count() - 1)
            if idx >= 0:
                self.setCurrentRecord(self.group.recordByIndex(idx))
            else:
                self.setCurrentRecord(None)
            self.display()

    def currentView(self):
        """
        Returns a reference to the current view.

        :return:
        """

        if self._currentView < 0:
            return None
        type = self._viewQueue.typeFromIndex(self._currentView)
        if not type in self.views:
            (ident, type) = self._viewQueue.viewFromType(type)
            self.addViewByIdAndType(ident, type)
        return self.views[type]

    # @brief Returns a dictionary with all field values for the current record.
    def get(self):
        if not self.currentRecord():
            return None
        self.currentView().store()
        return self.currentRecord().get()

    def isModified(self):
        """
        Returns True if any record has been modified. Returns False otherwise.

        :return:
        """
        if not self.currentRecord():
            return False
        self.currentView().store()
        res = False
        if self.currentView().showsMultipleRecords():
            return self.group.isModified()
        else:
            return self.currentRecord().isModified()

    def remove(self, unlink=False):
        """
        Removes all selected ids.

        :param unlink: If unlink is False (the default) records are only removed
        from the list.
        :type unlink: bool
        :return:If unlink is True records will be removed from the server too.
        :rtype: bool
        """
        records = self.selectedRecords()
        if unlink and records:
            # Remove records with id None as they would cause an exception
            # trying to remove from the server
            idsToUnlink = [x.id for x in records if x.id != None]
            # It could be that after removing records with id == None
            # there are no records to remove from the database. That is,
            # all records that should be removed are new and not stored yet.
            if idsToUnlink:
                unlinked = self.rpc.unlink(idsToUnlink)
                # Try to be consistent with database
                # If records could not be removed from the database
                # don't remove them on the client. Don't report it directly
                # though as probably an exception (Warning) has already
                # been shown to the user.
                if not unlinked:
                    return False

        if records:
            # Set no current record, so refreshes in the middle of the removal
            # process (caused by signals) do not crash.
            # Note that we want to ensure there are ids to remove so we don't
            # setCurrentRecord(None) if it's not strictly necessary.
            idx = self._currentRecordPosition
            self.setCurrentRecord(None)
            self.group.remove(records)
            if self.group.count():
                idx = min(idx, self.group.count() - 1)
                self.setCurrentRecord(self.group.recordByIndex(idx))
            else:
                self.setCurrentRecord(None)
        self.display()
        if records:
            return True
        else:
            return False

    def load(self, ids, addOnTop=False):
        """
        Loads the given ids to the RecordGroup and refreshes the view.
        :param ids:
        :param addOnTop:
        :return:
        """
        self.currentView().reset()
        self.group.load(ids, addOnTop)
        if ids:
            self.display(ids[0])
        else:
            self.setCurrentRecord(None)
            self.display()

    def display(self, id=None):
        """
        Displays the record with id 'id' or refreshes the current record if
        no id is given.

        :param id:
        :return:
        """

        if id:
            self.setCurrentRecord(self.group[id])
        if self.views:
            self.currentView().setReadOnly(self.isReadOnly())
            self.currentView().display(self.currentRecord(), self.group)

    def displayNext(self):
        """
        Moves current record to the next one in the list and displays it in the
        current view.
        :return: None
        """
        self.currentView().store()
        if self.group.recordExists(self.currentRecord()):
            idx = self.group.indexOfRecord(self.currentRecord())
            idx = (idx + 1) % self.group.count()
            self.setCurrentRecord(self.group.modelByIndex(idx))
        else:
            self.setCurrentRecord(
                self.group.count() and self.group.modelByIndex(0) or None)
        if self.currentRecord():
            self.currentRecord().setValidate()
        self.display()

    def displayPrevious(self):
        """
        Moves current record to the previous one in the list and displays it
        in the current view.
        :return: None
        """

        self.currentView().store()
        if self.group.recordExists(self.currentRecord()):
            #idx = self.group.records.index(self.currentRecord())-1
            idx = self.group.indexOfRecord(self.currentRecord()) - 1
            if idx < 0:
                idx = self.group.count() - 1
            self.setCurrentRecord(self.group.modelByIndex(idx))
        else:
            self.setCurrentRecord(
                self.group.count() and self.group.modelByIndex(-1) or None)

        if self.currentRecord():
            self.currentRecord().setValidate()
        self.display()

    def selectedIds(self):
        """
        Returns all selected record ids.

        Note that if there are new unsaved records, they might all have
        ID=None. You're probably looking for selectedRecords() function.

        see selectedRecords
        :return:
        """

        records = self.currentView().selectedRecords()
        ids = [record.id for record in records]
        return ids

    def selectedRecords(self):
        """
        Returns all selected records
        :return:
        """
        return self.currentView().selectedRecords()

    def currentId(self):
        """
        Returns the current record id.
        :return:
        """
        if self.currentRecord():
            return self.currentRecord().id
        else:
            return None

    def clear(self):
        """
        Clears the list of records and refreshes the view.

        Note that this won't remove the records from the database. But clears
        the records from the model. It means that sometimes you might want to
        use setRecordGroup( None ) instead of calling clear(). This is what
        OneToMany and ManyToMany widgets do, for example.
        see remove()
        :return:
        """
        self.group.clear()
        self.display()

    def storeViewSettings(self):
        """
        Stores settings of all opened views
        :return:
        """
        for view in list(self.views.values()):
            ViewSettings.store(view.id, view.viewSettings())

# vim:noexpandtab:
