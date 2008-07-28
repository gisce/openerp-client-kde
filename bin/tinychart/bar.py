#   Copyright (C) 2008 by Albert Cervera i Areny
#   albert@nan-tic.com
#
#   This program is free software; you can redistribute it and/or modify 
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or 
#   (at your option) any later version. 
#
#   This program is distributed in the hope that it will be useful, 
#   but WITHOUT ANY WARRANTY; without even the implied warranty of 
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License 
#   along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   59 Temple Place - Suite 330, Boston, MA  02111-1307, USA. 

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from abstractchart import *


class BarChartBar(QGraphicsRectItem):
	def __init__(self, parent):
		QGraphicsRectItem.__init__(self, parent)
		self.labelId = None

class AxisItem(QGraphicsPathItem):
	def __init__(self, parent):
		QGraphicsPathItem.__init__(self, parent)
		self._minimum = 0
		self._maximum = 10
		self._labels = None
		self._orientation = Qt.Vertical
		self._size = 100
		self._items = []

	def setMinimum( self, minimum ):
		self._minimum = minimum
		self.updatePath()
	
	def setMaximum( self, maximum ):
		self._maximum = maximum
		self.updatePath()

	def setLabels( self, labels ):
		self._labels = labels
		self.updatePath()

	def setSize( self, size ):
		self._size = size
		self.updatePath()

	def setOrientation( self, orientation ):
		self._orientation = orientation
		self.updatePath()

	def clear(self):
		for item in self._items:
			item.setParentItem( None )
			del item
		self._items = []

	def updatePath(self):
		self.clear()
		if self._minimum > self._maximum:
			tmp = self._maximum
			self._maximum = self._minimum
			self._minimum = tmp
		path = QPainterPath()	
		path.moveTo( 0, 0 )
		if self._orientation == Qt.Vertical:
			path.lineTo( 0, self._size )
		else:
			path.lineTo( self._size, 0 )

		diff = self._maximum - self._minimum
		if self._labels:
			items = len(self._labels)
		else:
			items = 10
		font = QFont()
		metrics = QFontMetrics( font )
		width = float(self._size) / items
		offset = width / 2
		for x in range(items):
			p = x * width
			item = QGraphicsSimpleTextItem( self )
			if self._orientation == Qt.Vertical:
				path.moveTo( -5, p )
				path.lineTo( 0, p )
				if self._labels:
					text = self._labels[x]
				else:
					text = '%.2f' % ( self._minimum + ( diff / items ) * ( items - x ) )
				item.setPos( -10 - metrics.width( text ), p - metrics.boundingRect(text).height() / 2.5 )
				item.setText( text )
			else:
				path.moveTo( p + offset, 5 )
				path.lineTo( p + offset, 0 )
				if self._labels:
					text = self._labels[x]
				else:
					text = '%.2f' % ( self._minimum + ( diff / items ) * ( items - x ) )
				item.setPos( p + offset, metrics.lineSpacing()  )
				item.setText( text )
				item.rotate( 45 )
			self._items.append( item )
		self.setPath( path )


class BarChart(AbstractChart):
	def __init__(self, parent=None):
		AbstractChart.__init__(self, parent)
		self.yAxis = AxisItem( self )
		self.xAxis = AxisItem( self )

	# Returns the total amount of bars 
	def barCount( self ):
		count = len(flatten(self._values))
		if not count:
			count = len(self._categories) * len(self._labels)
		if not count:
			count = 1
		return count

	def separatorCount( self ):
		return len(self._categories) - 1

	def separatorWidth( self ):
		defaultWidth = 5
		if self.separatorCount() * defaultWidth >= self.width():
			return 0
		else:
			return defaultWidth
		
	def barWidth( self ):
		return ( self.width() - self.separatorWidth() * self.separatorCount() ) / float(self.barCount())

	def updateChart(self):
		self.clear()
		if len(flatten(self._values)):
			maximum = max(flatten(self._values))
			if float(maximum) == 0.0:
				maximum = 1.0
		lastPosition = 0
		maximumHeight = self.height()
		barWidth = self.barWidth()
		separatorWidth = self.separatorWidth()
		for i in range(len(self._values)):
			manager = ColorManager( len(self._values[i]) )
			for j in range(len(self._values[i])):
				value = self._values[i][j]
				height = ( value / maximum ) * maximumHeight

				item = BarChartBar( self )
				item.labelId = i
				item.setBrush( manager.brush(j) )
				item.setPen( manager.pen(j) )
				item.setRect( lastPosition, maximumHeight - height, barWidth, height )
				self.addToGroup( item )
				self._items.append( item )

				lastPosition += barWidth
			lastPosition += separatorWidth

		if len(flatten(self._values)):
			self.yAxis.setMinimum( min(flatten(self._values)) )
			self.yAxis.setMaximum( max(flatten(self._values)) )
		else:
			self.yAxis.setMinimum( 0 )
			self.yAxis.setMaximum( 10 )
		self.yAxis.setOrientation( Qt.Vertical )
		self.yAxis.setSize( maximumHeight )
		self.yAxis.setZValue( 1 )
		self.addToGroup( self.yAxis )

		self.xAxis.setLabels( self._categories )
		self.xAxis.setOrientation( Qt.Horizontal )
		self.xAxis.setSize( self.width() )
		self.xAxis.setPos( 0, maximumHeight )
		self.xAxis.setZValue( 1 )
		self.addToGroup( self.xAxis )

		self.updateToolTips()
		self._legend.place()

	def setCategories( self, categories ):
		self._categories = categories
		self.xAxis.setLabels( self._categories )

	def setData( self, data ):
		# Admited data structure:
		# [ { 'name': 'A', 'values': {'group_a': 2} }, { 'name': 'B', 'values': {'group_b': 8} } ]
		categories = []
		labels = []
		if data:
			for x in data:
				categories.append( x['name'] )
			for y in data[0].keys():
				labels.append( y )
			categories.sort()
		self.setCategories( categories )
		self.setLabels( labels )
		values = []
		for x in data:
			value = []
			for y in labels:
				value.append( x['values'][y] )
			values.append( value )	
		self.setValues( values )
