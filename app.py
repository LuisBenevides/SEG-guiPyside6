

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import cv2 as cv2
from matplotlib import pyplot as plt

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from functions import *
import matplotlib.backends.backend_qt5 as backend


class MplToolbar(NavigationToolbar2QT):
    def __init__(self, canvas_, parent_):
        backend.figureoptions = None
        self.toolitems = (
            ('Home', 'Reset original view', 'home', 'home'),
            ('Back', 'Back to previous view', 'back', 'back'),
            ('Forward', 'Forward to next view', 'forward', 'forward'),
            (None, None, None, None),
            ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
            ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
            (None, None, None, None),
            ('Save', 'Save the current image', 'filesave', 'save_figure'),
            )
        NavigationToolbar2QT.__init__(self, canvas_, parent_)

fileName_global = "../tomografias/000100.dcm"
dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))

# fileName_global = ""
varpos = 1.0

COLORS = [
    # https://lospec.com/palette-list/6-bit-12-colour-challenge
    '#ffeeb9',
    '#bd4b4b',
    '#442242',
    '#1ab11d',
    '#286440',
    '#133542',
    '#675c85',
    '#251e3c',
    '#1e132c',
    '#b5b4d3',
    '#6b6a7c',
    '#232328'
]


class QPaletteButton(QPushButton):

    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(50, 50))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)


class PlotWidget(QWidget):
    def __init__(self):
        super().__init__()
        #  create widgets
        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        self.toolbar = MplToolbar(self.view, self)
        #  Create layout
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout)

        self.on_change()

    def on_change(self):
        global fileName_global
        fileName_global

        """ Update the plot with the current input values """
        if fileName_global != '':
            self.dicom_image = dicom2array(pydicom.dcmread(fileName_global, force=True))

        self.axes.clear()

        if fileName_global != '':
            self.axes.imshow(self.dicom_image, cmap='gray')
            self.view.draw()


class PlotWidgetOriginal(QWidget):
    def __init__(self):
        super().__init__()

        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        self.toolbar = MplToolbar(self.view, self)
        self.view.mpl_connect('button_press_event', mouse_event)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout)

        self.on_change()

    def HistMethodClahe(self):
        global dicom_image_array
        global fileName_global
        """ Update the plot with the current input values """
        if fileName_global != '':
            dicom_image_array = select_RoI(dicom_image_array)
            dicom_image_array = ConvertToUint8(dicom_image_array)

        dicom_image_array = exposure.equalize_adapthist(dicom_image_array, clip_limit=0.03)

        self.axes.clear()
        self.axes.imshow(dicom_image_array, cmap='gray')
        self.view.draw()

    def SuperPixel(self):
        global dicom_image_array
        global fileName_global
        sigma_slic = 1
        compactness = 0.05
        numSegments = 2000
        method = 'gaussian'
        # apply SLIC and extract (approximately) the supplied number of segments
        segments = slic(dicom_image_array, n_segments=numSegments, sigma=sigma_slic, \
                        multichannel=False, compactness=compactness, start_label=1)
        self.axes.clear()
        self.axes.imshow(mark_boundaries(dicom_image_array, segments))
        self.view.draw()

        for (i, segVal) in enumerate(np.unique(segments)):
            # construct a mask for the segment
            mask = np.zeros(dicom_image_array.shape[:2], dtype="uint8")
            mask[segments == segments[300][200]] = 255
            # show the masked region
            cv2.imshow("Mask", mask)
            cv2.imshow("Applied", cv2.bitwise_and(dicom_image_array, dicom_image_array, mask=mask))
            cv2.waitKey(0)

    def on_change(self):
        global dicom_image_array
        global fileName_global
        dicom_image_array = ConvertToUint8(dicom_image_array)
        """ Update the plot with the current input values """
        # if fileName_global != '': 
        #     self.dicom_image = dicom2array(pydicom.dcmread(fileName_global , force = True))
        self.axes.clear()

        if fileName_global != '':
            self.axes.imshow(dicom_image_array, cmap='gray')
            self.view.draw()

    def ResetDicom(self):
        global dicom_image_array
        global fileName_global
        if fileName_global != '':
            dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
            dicom_image_array = select_RoI(dicom_image_array)
            dicom_image_array = ConvertToUint8(dicom_image_array)
        self.axes.imshow(dicom_image_array, cmap='gray')
        self.view.draw()


class Canvas(QLabel):

    def __init__(self, image_dir):
        super().__init__()
        image = QImage(image_dir)
        pixmap = QPixmap(QPixmap.fromImage(image))
        self.setPixmap(pixmap)

        self.last_x, self.last_y = None, None
        self.pen_color = QColor('#000000')

    def set_pen_color(self, c):
        self.pen_color = QColor(c)

    def mouseMoveEvent(self, e):
        if self.last_x is None:  # First event.
            self.last_x = e.x()
            self.last_y = e.y()
            return  # Ignore the first time.

        canvas = self.pixmap()
        painter = QPainter(canvas)
        p = painter.pen()
        p.setWidth(3)
        p.setColor(self.pen_color)
        painter.setPen(p)
        if e.x() > 0 and e.y() > 0:
            painter.drawPoint(e.x() / varpos, e.y() / varpos)
            print(e.x() / varpos)
            print(e.y() / varpos)
        painter.end()
        self.setPixmap(canvas)

        # Update the origin for next time.
        self.last_x = e.x()
        self.last_y = e.y()

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None


class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()

        self.bar = self.addToolBar("Menu")
        self.bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.color_action = QAction(self)
        self.color_action.triggered.connect(self.on_color_clicked)
        # self.bar.addAction(self.color_action)
        self.set_color(Qt.black)

        self.plotwidget = PlotWidget()
        self.plotwidget_original = PlotWidgetOriginal()

        self.layout = QHBoxLayout()
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        layout2.addWidget(self.plotwidget_original)

        self.layout.addLayout(layout2)
        layout3.addWidget(self.plotwidget)

        self.layout.addLayout(layout3)
        # self.layout.addWidget(self.imageLabel)

        palette = QHBoxLayout()
        self.add_palette_buttons(palette)

        main_widget = QWidget()
        main_widget.setLayout(self.layout)
        self.setCentralWidget(main_widget)

        ###################################

        self.createActions()
        self.createMenus()
        self.setGeometry(600, 600, 600, 600)
        self.setWindowTitle("- LAMAC -")

    @Slot()
    def on_color_clicked(self, layout):

        color = QColorDialog.getColor(Qt.black, self)
        if color:
            self.set_color(color)

    def set_color(self, color: QColor = Qt.black):
        # Create color icon
        pix_icon = QPixmap(20, 20)
        pix_icon.fill(color)

        self.color_action.setIcon(QIcon(pix_icon))
        # self.imageLabel.set_pen_color(color)
        # self.color_action.setText(QColor(color).name())

    def add_palette_buttons(self, layout):
        for c in COLORS:
            b = QPaletteButton(c)
            b.pressed.connect(lambda c=c: self.imageLabel.set_pen_color(c))
            layout.addWidget(b)

    def open(self):
        global fileName_global
        global dicom_image_array
        fileName_global = self.pathFile()
        dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
        dicom_image_array = select_RoI(dicom_image_array)
        self.plotwidget_original.on_change()
        self.plotwidget.on_change()

    def pathFile(self):
        fileName_global, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                         QDir.currentPath(), filter="DICOM (*.dcm *.)")
        return fileName_global

    def view(self, fileName):
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
        image = dicom2array(pydicom.dcmread(fileName_global, force=True))
        img_eq = exposure.equalize_hist(image)
        imsave('./tempH.png', (img_eq * 255).astype(np.uint8))
        fileName = "./tempH.png"
        self.view(fileName)

    def HistMethodCLAHE(self):
        self.plotwidget_original.HistMethodClahe()

    def SuperPixel(self):
        self.plotwidget_original.SuperPixel()

    def OriginalImage(self):
        self.plotwidget_original.ResetDicom()

    def about(self):
        QMessageBox.about(self, "LAMAC",
                          "<p>Segmentador Manual !!! </p>")

    def the_button_was_clicked(self):
        self.SuperPixel()

    def createActions(self):
        self.openAct = QtGui.QAction("&Open...", self, shortcut="Ctrl+O",
                                     triggered=self.open)
        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                                     triggered=self.close)

        self.normalSizeAct = QtGui.QAction("&Normal Size", self,
                                           shortcut="Ctrl+S", enabled=False, triggered=self.normalSize)

        self.fitToWindowAct = QtGui.QAction("&Fit to Window", self,
                                            enabled=False, checkable=True, shortcut="Ctrl+F",
                                            triggered=self.fitToWindow)

        self.HistMethodAct = QtGui.QAction("&HistMethod", self,
                                           enabled=False, checkable=False,
                                           triggered=self.HistMethod)
        self.HistMethodCLAHEAct = QtGui.QAction("&Hist CLAHE", self,
                                                triggered=self.HistMethodCLAHE)
        self.SuperPixelAct = QtGui.QAction("&SuperPixel", self,
                                           triggered=self.SuperPixel)
        self.OriginalImageAct = QtGui.QAction("&Original Image", self,
                                              triggered=self.OriginalImage)
        self.aboutAct = QtGui.QAction("&About", self, triggered=self.about)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                                        triggered=qApp.aboutQt)

    def createMenus(self):
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        # self.viewMenu.addAction(self.zoomInAct)
        # self.viewMenu.addAction(self.zoomOutAct)
        self.viewMenu.addAction(self.normalSizeAct)
        self.viewMenu.addAction(self.HistMethodAct)
        self.viewMenu.addAction(self.HistMethodCLAHEAct)
        self.viewMenu.addAction(self.SuperPixelAct)
        self.viewMenu.addAction(self.OriginalImageAct)
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.fitToWindowAct)

        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.helpMenu)

    def updateActions(self):
        # self.zoomOutAct.setEnabled(not self.fitToWindowAct.isChecked())
        # self.zoomInAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.normalSizeAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.HistMethodAct.setEnabled(not self.fitToWindowAct.isChecked())
        self.HistMethodCLAHEAct.setEnabled(not self.fitToWindowAct.isChecked())

    def scaleImage(self, factor):
        self.scaleFactor *= factor
        self.imageLabel.resize(self.scaleFactor * self.imageLabel.pixmap().size())

        self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), factor)
        self.adjustScrollBar(self.scrollArea.verticalScrollBar(), factor)
    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec())
