#!/usr/bin/env python

#############################################################################
##
## Copyright (C) 2005-2005 Trolltech AS. All rights reserved.
##
## This file is part of the example classes of the Qt Toolkit.
##
## This file may be used under the terms of the GNU General Public
## License version 2.0 as published by the Free Software Foundation
## and appearing in the file LICENSE.GPL included in the packaging of
## this file.  Please review the following information to ensure GNU
## General Public Licensing requirements will be met:
## http://www.trolltech.com/products/qt/opensource.html
##
## If you are unsure which license is appropriate for your use, please
## review the following information:
## http://www.trolltech.com/products/qt/licensing.html or contact the
## sales department at sales@trolltech.com.
##
## This file is provided AS IS with NO WARRANTY OF ANY KIND, INCLUDING THE
## WARRANTY OF DESIGN, MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.
##
#############################################################################

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from skimage import data, img_as_float
from skimage import exposure
import pydicom
from pydicom.data import get_testdata_files
import numpy as np
from skimage.io import imsave
fileName_global = ""

class MyScrollArea(QScrollArea):
    def __init__(self, imageLabel):
        super().__init__()
        self.setWidget(imageLabel)
        self.myImageWidget = imageLabel
        self.oldScale = 1
        self.newScale = 1
        imageLabel.setScaledContents(True)
    def wheelEvent(self, event) -> None:
        if event.angleDelta().y() < 0:
            # zoom out
            self.newScale = 0.8
        else:
            # zoom in
            self.newScale = 1.25

        widgetPos = self.myImageWidget.mapFrom(self, event.position())

        # resize image
        self.myImageWidget.resize(self.myImageWidget.size() * self.newScale)

        delta = widgetPos * self.newScale - widgetPos
        self.horizontalScrollBar().setValue(
            self.horizontalScrollBar().value() + delta.x())
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() + delta.y())
        
        self.oldScale = self.newScale


    
def dicom2array(dcm):
    img_raw = np.float64(dcm.pixel_array)
    output = np.array( dcm.RescaleSlope * img_raw + dcm.RescaleIntercept, dtype=int )
    return output

class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()
        # self.scaleFactor = 0.0
      
        self.imageLabel = QLabel() 
        self.imageLabel.installEventFilter(self)
            
        # self.imageLabel.setBackgroundRole(QtGui.QPalette.Base)
        # self.imageLabel.setSizePolicy(QSizePolicy.Ignored,
        #         QSizePolicy.Ignored)
        self.imageLabel.setAlignment(QtCore.Qt.AlignVCenter)

        cursor = Qt.CrossCursor
        self.imageLabel.setCursor(cursor)
        

        # self.setMinimumHeight(600)
        # self.setMinimumWidth(600)
        # self.setMaximumHeight(800)
        # self.setMaximumWidth(800)
        

        # self.scrollArea = QScrollArea()
        # self.scrollArea.setBackgroundRole(QtGui.QPalette.Dark)
        # self.scrollArea.setWidget(self.imageLabel)
        self.scrollArea = MyScrollArea(self.imageLabel)

        # insert to layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.scrollArea)
        self.setLayout(self.layout)



        self.setCentralWidget(self.scrollArea)

        self.createActions()
        self.createMenus()
        self.setGeometry(600,600,600,600)
        self.setWindowTitle("- LAMAC -")

    def open(self):
        global fileName_global 
        fileName_global = self.pathFile()
        cvImg = dicom2array(pydicom.dcmread(fileName_global , force = True))
        imsave('./temp1.png',cvImg)
        fileName="./temp1.png"
        if fileName:
           self.view(fileName)

    def pathFile(self):
        fileName_global,_ = QFileDialog.getOpenFileName(self, "Open File",
                QDir.currentPath(),filter ="DICOM (*.dcm *.)")
        return fileName_global

    def view(self,fileName): 
        image = QImage(fileName)
        if image.isNull():
            QMessageBox.information(self, "Image",
                    "Cannot load %s." % fileName)
            return
        self.imageLabel.setPixmap(QPixmap.fromImage(image))
        self.scaleFactor = 1.0
        self.fitToWindowAct.setEnabled(True)
        self.updateActions()
        if not self.fitToWindowAct.isChecked():
            self.imageLabel.adjustSize()

    def zoomIn(self):
        self.scaleImage(1.25)

    def zoomOut(self):
        self.scaleImage(0.8)

    def normalSize(self):
        self.imageLabel.adjustSize()
        self.scaleFactor = 1.0

    def fitToWindow(self):
        fitToWindow = self.fitToWindowAct.isChecked()
        self.scrollArea.setWidgetResizable(fitToWindow)
        if not fitToWindow:
            self.normalSize()

        self.updateActions()
    
    def HistMethod(self):
        # Equalization
        print(fileName_global)
        image = dicom2array(pydicom.dcmread(fileName_global , force = True))
        img_eq = exposure.equalize_hist(image)
        imsave('./tempH.png',img_eq)
        fileName="./tempH.png"
        self.view(fileName)

    def about(self):
        QMessageBox.about(self, "About Image Viewer",
                "<p>The <b>Image Viewer</b> example shows how to combine "
                "QLabel and QScrollArea to display an image. QLabel is "
                "typically used for displaying text, but it can also display "
                "an image. QScrollArea provides a scrolling view around "
                "another widget. If the child widget exceeds the size of the "
                "frame, QScrollArea automatically provides scroll bars.</p>"
                "<p>The example demonstrates how QLabel's ability to scale "
                "its contents (QLabel.scaledContents), and QScrollArea's "
                "ability to automatically resize its contents "
                "(QScrollArea.widgetResizable), can be used to implement "
                "zooming and scaling features.</p>"
                "<p>In addition the example shows how to use QPainter to "
                "print an image.</p>")

    def createActions(self):
        self.openAct = QtGui.QAction("&Open...", self, shortcut="Ctrl+O",
                triggered=self.open)
        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                triggered=self.close)

        self.zoomInAct = QtGui.QAction("Zoom &In (25%)", self,
                shortcut="Ctrl++", enabled=False, triggered=self.zoomIn)

        self.zoomOutAct = QtGui.QAction("Zoom &Out (25%)", self,
                shortcut="Ctrl+-", enabled=False, triggered=self.zoomOut)

        self.normalSizeAct = QtGui.QAction("&Normal Size", self,
                shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QtGui.QAction("&Fit to Window", self,
                enabled=False, checkable=True, shortcut="Ctrl+F",
                triggered=self.fitToWindow)

        self.HistMethodAct = QtGui.QAction("&HistMethod", self,
                enabled=False, checkable=False,
                triggered=self.HistMethod)

        self.aboutAct = QtGui.QAction("&About", self, triggered=self.about)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                triggered= qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.zoomInAct)
        self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.HistMethodAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.HistMethodAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)

        self.zoomInAct.setEnabled(self.scaleFactor < 3.0)
        self.zoomOutAct.setEnabled(self.scaleFactor > 0.333)

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                                + ((factor - 1) * scrollBar.pageStep()/2)))


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
 

    sys.exit(app.exec_())#!/usr/bin/env python