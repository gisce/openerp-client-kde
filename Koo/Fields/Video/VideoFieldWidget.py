##############################################################################
#
# Copyright (c) 2008 Albert Cervera i Areny <albert@nan-tic.com>
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


from Koo.Common import Common
from PyQt5.QtWidgets import *

from Koo.Fields.AbstractFieldWidget import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

try:
    from PyQt5.phonon import *
    phononAvailable = True
except:
    phononAvailable = False
    pass


(VideoFieldWidgetUi, VideoFieldWidgetBase) = loadUiType(Common.uiPath('video.ui'))


class VideoFieldWidget(AbstractFieldWidget, VideoFieldWidgetUi):
    def __init__(self, parent, view, attrs={}):
        AbstractFieldWidget.__init__(self, parent, view, attrs)
        VideoFieldWidgetUi.__init__(self)
        self.setupUi(self)

        if phononAvailable:
            self.layout().removeWidget(self.uiVideo)
            self.uiVideo.setParent(None)
            self.uiVideo = Phonon.VideoPlayer(Phonon.VideoCategory, self)
            self.uiVideo.setSizePolicy(
                QSizePolicy.Preferred, QSizePolicy.Expanding)
            self.uiVideo.show()
            self.layout().addWidget(self.uiVideo)
            self.uiSlider = Phonon.SeekSlider(self)
            self.layout().addWidget(self.uiSlider)

        self.installPopupMenu(self.uiVideo)

        self.pushPlay.clicked.connect(self.play)
        self.pushPause.clicked.connect(self.pause)
        self.pushStop.clicked.connect(self.stop)
        self.pushLoad.clicked.connect(self.loadVideo)
        self.pushSave.clicked.connect(self.save)
        self.pushRemove.clicked.connect(self.remove)

    def loadVideo(self):
        try:
            filename = QFileDialog.getOpenFileName(
                self, _('Select the file to attach'))[0]
            if filename.isNull():
                return
            if self.isBinary():
                filename = str(filename)
                value = file(filename).read()
                self.record.setValue(self.name, value)
            else:
                self.record.setValue(self.name, str(filename))
        except:
            QMessageBox.information(
                self, _('Error'), _('Error reading the file'))

    def save(self):
        filename = QFileDialog.getSaveFileName(self, _('Save as...'))[0]
        try:
            if filename:
                fp = file(filename, 'wb+')
                fp.write(self.record.value(self.name))
                fp.close()
        except:
            QMessageBox.information(
                self, _('Error'), _('Error writing the file!'))
        Semantic.addInformationToFile(
            filename, self.record.group.resource, self.record.id, self.name)

    def remove(self):
        self.clear()
        self.record.setValue(self.name, False)
        self.modified()

    def play(self):
        if self.uiVideo.isPaused():
            self.uiVideo.play()
            return

        self.stop()
        value = self.record.value(self.name)
        if not value:
            return
        if self.isBinary():
            media = Phonon.MediaSource(QBuffer(QByteArray(value)))
        else:
            media = Phonon.MediaSource(value)

        self.uiVideo.play(media)
        self.uiVideo.show()
        self.uiSlider.setMediaObject(self.uiVideo.mediaObject())
        self.uiSlider.show()

    def pause(self):
        self.uiVideo.pause()

    def stop(self):
        self.uiVideo.stop()
        self.uiVideo.hide()
        self.uiSlider.hide()

    def storeValue(self):
        pass

    def clear(self):
        self.stop()
        self.updateButtons()

    def showValue(self):
        self.stop()
        self.updateButtons()

    def setReadOnly(self, value):
        AbstractFieldWidget.setReadOnly(self, value)
        self.pushLoad.setEnabled(not value)

    def isBinary(self):
        if self.attrs['type'] == 'binary':
            return True
        else:
            return False

    def updateButtons(self):
        if not self.isReadOnly() and self.record and self.record.value(self.name):
            canPlay = True
        else:
            canPlay = False
        self.pushPlay.setEnabled(canPlay)
        self.pushStop.setEnabled(canPlay)
        self.pushPause.setEnabled(canPlay)
        self.pushSave.setEnabled(canPlay)
        self.pushRemove.setEnabled(canPlay)
        if self.isReadOnly():
            self.pushLoad.setEnabled(False)
        else:
            self.pushLoad.setEnabled(True)
