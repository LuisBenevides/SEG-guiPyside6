from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import cv2 as cv2
from matplotlib import pyplot as plt
from skimage.segmentation import mark_boundaries
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas
from functions import *
import copy
from PIL import Image
from os import path

# The superpixel mask is here
segments_global = []
# The Painted(rgb) mask is here
mask3d  = []
# The backups mask3d is here. Is used to rollback in case of wrong paints.
previous_paints = []
# Defines if the paint are enabled
superpixel_auth = False
# Defines the current color of the superpixel paint
colorvec = np.array([0, 0, 0])
# Defines if the 'mask3d' or 'masks' variables needs to be created again
masks_empty = True
# Click event for paint superpixel
def mouse_event(event):
    global segments_global
    global superpixel_auth
    if ((event.xdata != None or event.ydata != None) 
    and ((event.xdata > 1 and event.ydata >1)) 
    and (superpixel_auth == True) 
    and (str(imageViewer.plotsuperpixelmask.toolbar._actions["zoom"]).__contains__("checked=false"))
    and (str(imageViewer.plotwidget_modify.toolbar._actions["zoom"]).__contains__("checked=false"))
    ):
        paintSuperPixel(event.xdata,event.ydata,segments_global)

def paintSuperPixel(x,y,segments):
    global masks
    # fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
    global mask3d 
    global previous_paints
    global colorvec
    global masks_empty
    if(masks_empty):
        # Creates a new 3d mask with the shape of the dicom image array
        mask3d = np.zeros((dicom_image_array.shape[0],dicom_image_array.shape[1],3), dtype = "uint8")
        mask3d[:,:,0] = 255 * dicom_image_array 
        mask3d[:,:,1] = 255 * dicom_image_array 
        mask3d[:,:,2] = 255 * dicom_image_array
        masks_empty = False
    masks = np.zeros_like(dicom_image_array, dtype="bool")
    # Store a copy of mask3d for rollback
    previous_paints.append(copy.deepcopy(mask3d))
    # Verify if exists more than 10 copies, for delete the older
    if(previous_paints.__len__() == 11):
            previous_paints.__delitem__(0) 
    # Verify what segments of segments global are equals to 
    # the clicked segment to change this masks elements to 1, 
    # instead of false
    masks[segments == segments[int(y)][int(x)]] = 1
    # show the masked region
    ## D_I_A = ((255 * dicom_image_array) * (~masks)).astype('uint8') 

    # Ranges the array, painting each layer of rgb with the color choosed
    # in the colorvec
    mask3d[:,:,0] = colorvec[0] * masks + mask3d[:,:,0]*(~masks).astype('uint8')
    mask3d[:,:,1] = colorvec[1] * masks + mask3d[:,:,1]*(~masks).astype('uint8')
    mask3d[:,:,2] = colorvec[2] * masks + mask3d[:,:,2]*(~masks).astype('uint8')
    
    # Update the mask with the new rgb mask(with the new painted superpixel)
    imageViewer.plotsuperpixelmask.UpdateView()

# Here are stored the path of the opened file    
fileName_global = ''    
# fileName_global = "C:/Users/LUIAN/Desktop/SegPy/SEG-guiPyside6/images/000003.dcm"
# dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
# dicom_image_array =  ConvertToUint8(dicom_image_array)

# Here are stored the array of the dicom image(both original, 
# with removed objects and with CLAHE applied)
dicom_image_array = []

masks =[]

COLORS = [
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

# Class of the toolbar of the ploted image
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
            ('Port', 'Back to the previous paint', "back", 'back_paint'),
            ('Save', 'Save the current image', 'filesave', 'save_mask'),
            )
        NavigationToolbar2QT.__init__(self, canvas_, parent_)
    # Function to save the mask to png
    def save_mask(self):
        # Prevent the error throwed by convert a empty array to an array
        if(not np.array_equal(mask3d, [])):
            file_number = 1

            # Converts the mask 3d to an image
            img = Image.fromarray(mask3d, 'RGB')
            
            # Chooses the correct name(according with the existing, adding
            # +1 to the number identify if this filename already exists)
            if(path.exists("mask.png")):
                while(path.exists(f'mask{str(file_number)}.png')):
                    file_number +=1

                img.save(f'mask{str(file_number)}.png')
            img.save('mask.png')

    # Rollbacks a state of the paint, copying the saved mask to the mask3d
    # deleting the copied and updating the view to the new mask with rollback
    def back_paint(self):
        global previous_paints 
        global mask3d

        # Checks if have backups of masks 3d to rollback
        if(previous_paints.__len__() >= 1):  
            # Copy the backup mask to the mask3d variable
            mask3d = copy.deepcopy(previous_paints[(previous_paints.__len__()-1)])
            # Delete the rollbacked mask
            previous_paints.__delitem__(previous_paints.__len__() -1)
            # Update the view
            imageViewer.plotsuperpixelmask.UpdateView()

# Class that shows the painted image
class PlotSuperPixelMask(QWidget):
    def __init__(self):
        super().__init__()
        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        # Includes the toolbar
        self.toolbar = MplToolbar(self.view, self)
        # Create the event associated with a function on click
        self.view.mpl_connect('button_press_event', mouse_event)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout) 
    # Update the view, displaying the mask3d(if modified, shows the new mask)
    def UpdateView(self):
        global mask3d
        if (not masks_empty):
            # Clear previous views
            self.axes.clear()
            # Shows the new view
            self.axes.imshow(mask3d, cmap='gray')
            self.view.draw()
    # Self explanatory
    def ClearView(self):
        self.axes.clear()


# Class that create the Pallete of collors to choose for paint
class QPaletteButton(QPushButton):

    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24,24))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)
# Not used in moment, but is very similar to 'PlotWidgetModify' class
class PlotWidgetOriginal(QWidget):
    def __init__(self):
        super().__init__()
        self.segments =[]
        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        
        self.toolbar = MplToolbar(self.view, self)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout)

        # self.on_change()

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
        global segments_global
        sigma_slic = 1
        compactness = 0.05
        numSegments = 2000
        method = 'gaussian'
        # apply SLIC and extract (approximately) the supplied number of segments
        segments_global = slic(dicom_image_array, n_segments=numSegments, sigma=sigma_slic, \
                        multichannel=False, compactness=compactness, start_label=1)
        self.axes.clear()
        self.axes.imshow(mark_boundaries(dicom_image_array, segments_global))
        self.view.draw()


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
            dicom_image_array = ConvertToUint8(dicom_image_array)
        self.axes.imshow(dicom_image_array, cmap='gray')
        self.view.draw()
    def DeleteObjects(self):
        global dicom_image_array
        global fileName_global
        if fileName_global != '':
            dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
            dicom_image_array = select_RoI(dicom_image_array)            
            dicom_image_array = ConvertToUint8(dicom_image_array)
        self.axes.imshow(dicom_image_array, cmap='gray')
        self.view.draw()




# Class that shows the tomography with 'remove objects', 'CLAHE' and 
# superpixels borders
class PlotWidgetModify(QWidget):
    # Very similar with 'PlotSuperpixelMask' class
    def __init__(self):
        super().__init__()
        self.segments =[]
        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        self.toolbar = MplToolbar(self.view, self)
        self.view.mpl_connect('button_press_event', mouse_event)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout)

        # self.on_change()

    # Self explanatory
    def ChangeSuperpixelAuth(self):
        global superpixel_auth
        superpixel_auth = False
    
    #  Apply the CLAHE method, that makes the tomography clearer
    def HistMethodClahe(self):
        global dicom_image_array
        global fileName_global
        # Just executes the method if exists an opened image
        if fileName_global != '':
            # Method that makes the CLAHE
            dicom_image_array = exposure.equalize_adapthist(dicom_image_array, clip_limit=0.03) 
            self.axes.clear()
            self.axes.imshow(dicom_image_array, cmap='gray')
            self.view.draw()
    
    # Apply the superpixel segmentation to the current dicom image array
    def SuperPixel(self):
        global dicom_image_array
        global fileName_global
        global segments_global
        global superpixel_auth
        sigma_slic = 1
        compactness = 0.05
        numSegments = 2000
        method = 'gaussian'
        # apply SLIC and extract (approximately) the supplied number of segments
        segments_global = slic(dicom_image_array, n_segments=numSegments, sigma=sigma_slic, \
                        multichannel=False, compactness=compactness, start_label=1)
        self.axes.clear()
        self.axes.imshow(mark_boundaries(dicom_image_array, segments_global))
        self.view.draw()
        superpixel_auth = True


    # Refresh the dicom image array
    def on_change(self):
        self.ChangeSuperpixelAuth()
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

    # Reset the dicom image array
    def ResetDicom(self):
        self.ChangeSuperpixelAuth()
        global dicom_image_array
        global fileName_global
        global superpixel_auth
        if fileName_global != '':
            # Read the dicom image again
            dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
            # Convert to uint8 to display again
            dicom_image_array = ConvertToUint8(dicom_image_array)
        self.axes.imshow(dicom_image_array, cmap='gray')
        self.view.draw()
        superpixel_auth = False

    # Apply the delete objects method(removes unwanted objects)
    def DeleteObjects(self):
        """This method reset the dicom image, reading the original image again.
        So, the CLAHE method needs to be applied after this method."""
        self.ChangeSuperpixelAuth()
        global dicom_image_array
        global fileName_global
        global superpixel_auth
        if fileName_global != '':
            dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
            # The function that makes the method
            dicom_image_array = select_RoI(dicom_image_array)            
            dicom_image_array = ConvertToUint8(dicom_image_array)

        self.axes.imshow(dicom_image_array, cmap='gray')
        self.view.draw()
        superpixel_auth = False

# Class that manage the layout of the window.
class ImageViewer(QMainWindow):
    def __init__(self):
        super(ImageViewer, self).__init__()

        self.bar = self.addToolBar("Menu")
        self.bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.color_action = QAction(self)
        self.color_action.triggered.connect(self.on_color_clicked)
        self.bar.addAction(self.color_action)
        self.set_color(Qt.black)

        # self.plotwidget_original = PlotWidgetOriginal()
        self.plotwidget_modify = PlotWidgetModify()
        
        self.plotsuperpixelmask = PlotSuperPixelMask()   
        self.layout = QHBoxLayout()
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # layout2.addWidget(self.plotwidget_original)
        layout2.addWidget(self.plotsuperpixelmask)

        self.layout.addLayout(layout2)
        layout3.addWidget(self.plotwidget_modify)

        self.layout.addLayout(layout3)
        # self.layout.addWidget(self.imageLabel)

        palette = QHBoxLayout()
        self.add_palette_buttons(palette)

        main_widget = QWidget()
        main_widget.setLayout(self.layout)
        self.setCentralWidget(main_widget)

        ###################################
        # palette = main_widget.QHBoxLayout()
        # self.add_palette_buttons(palette)
        # self.layout.addLayout(palette)
        
        self.createActions()
        self.createMenus()
        self.setGeometry(250, 100, 1000, 600)
        self.setWindowTitle("- LAMAC -")

    @Slot()
    def on_color_clicked(self, layout):
        global colorvec
        color = QColorDialog.getColor(Qt.black, self)
        qcolor = QColor(color)
        colorvec = np.array([qcolor.red(), qcolor.green(), qcolor.blue()])
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
            b.pressed.connect(lambda c=c: self.canvas.set_pen_color(c))
    def open(self):
        global fileName_global
        global dicom_image_array
        global mask3d
        global masks_empty
        fileName_global = self.pathFile()
        dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
        dicom_image_array =  ConvertToUint8(dicom_image_array)
        # self.plotwidget_original.on_change()
        self.plotwidget_modify.on_change()
        mask3d = []
        masks_empty = True
        imageViewer.plotsuperpixelmask.UpdateView()

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

    def HistMethodCLAHE(self):
        # self.plotwidget_original.HistMethodClahe()
        self.plotwidget_modify.HistMethodClahe()

    def SuperPixel(self):
        # self.plotwidget_original.SuperPixel()
        self.plotwidget_modify.SuperPixel()
        self.plotsuperpixelmask.UpdateView()
    def OriginalImage(self):
        # self.plotwidget_original.ResetDicom()
        self.plotwidget_modify.ResetDicom()
    def RemoveObjects(self):
        # self.plotwidget_original.DeleteObjects()
        self.plotwidget_modify.DeleteObjects()     
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

        # self.HistMethodAct = QtGui.QAction("&HistMethod", self,
        #                                    enabled=False, checkable=False,
        #                                    triggered=self.HistMethod)
        self.HistMethodCLAHEAct = QtGui.QAction("&Hist CLAHE", self,
                                                triggered=self.HistMethodCLAHE)
        self.SuperPixelAct = QtGui.QAction("&SuperPixel", self,
                                           triggered=self.SuperPixel)
        self.OriginalImageAct = QtGui.QAction("&Original Image", self,
                                              triggered=self.OriginalImage)
        self.RemoveObjectsAct = QtGui.QAction("&Remove Objects", self,
                                              triggered=self.RemoveObjects)
        
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
        # self.viewMenu.addAction(self.HistMethodAct)
        self.viewMenu.addAction(self.HistMethodCLAHEAct)
        self.viewMenu.addAction(self.SuperPixelAct)
        self.viewMenu.addAction(self.OriginalImageAct)
        self.viewMenu.addAction(self.RemoveObjectsAct)
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
