from PySide6 import QtCore, QtGui, QtWidgets
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
colorvec = np.array([255, 255, 0])
# Defines if the 'mask3d' or 'masks' variables needs to be created again
masks_empty = True
# Aproximated number of superpixels segments
numSegments = 2000
segmentedMask =[]
currentTissue = 0
informacoes = {"colors":[], "identifier":[], "tissue":[]}
previous_segments = {"superpixel":[], "previous_identifier":[]}
dictTissues = {"Fat":1, "Bone":2, "Muscle":3}
# Click event for paint superpixel
def mouse_event(event):
    global segments_global
    global superpixel_auth
    if ((event.xdata != None or event.ydata != None) 
    and ((event.xdata > 1 and event.ydata >1)) 
    and (superpixel_auth == True) 
    and (str(imageViewer.plotsuperpixelmask.toolbar._actions["zoom"]).__contains__("checked=false"))
    and (str(imageViewer.plotwidget_modify.toolbar._actions["zoom"]).__contains__("checked=false"))
    and (str(imageViewer.plotsuperpixelmask.toolbar._actions["pan"]).__contains__("checked=false"))
    and (str(imageViewer.plotwidget_modify.toolbar._actions["pan"]).__contains__("checked=false"))
    ): 
        paintSuperPixel(event.xdata,event.ydata,segments_global)

def paintSuperPixel(x,y,segments):
    global masks
    # fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
    global mask3d 
    global previous_paints
    global previous_segments
    global colorvec
    global masks_empty
    global segmentedMask
    global informacoes
    global currentTissue
    if(np.array_equal(segmentedMask, [])):
        segmentedMask = np.zeros_like(dicom_image_array, dtype="uint8")
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
    previous_segments["superpixel"].append(segments[int(y)][int(x)])
    previous_segments["previous_identifier"].append(segmentedMask[int(y)][int(x)])
    # Verify if exists more than 10 copies, for delete the older
    if(previous_paints.__len__() == 11):
            previous_paints.__delitem__(0)
            previous_segments["superpixel"].__delitem__(0)
            previous_segments["previous_identifier"].__delitem__(0)
    segmentedMask[segments==segments[int(y)][int(x)]] = currentTissue        
    # Verify what segments of segments global are equals to 
    # the clicked segment to change this masks elements to 1, 
    # instead of false
    masks[segments == segments[int(y)][int(x)]] = 1
    # show the masked region
    ## D_I_A = ((255 * dicom_image_array) * (~masks)).astype('uint8') 

    mask3d[:,:,0] = informacoes['colors'][currentTissue -1][0] * masks + mask3d[:,:,0]*(~masks).astype('uint8')
    mask3d[:,:,1] = informacoes['colors'][currentTissue -1][1] * masks + mask3d[:,:,1]*(~masks).astype('uint8')
    mask3d[:,:,2] = informacoes['colors'][currentTissue -1][2] * masks + mask3d[:,:,2]*(~masks).astype('uint8')
    
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
        global segmentedMask
        informacoesLista = []
        for i in range(informacoes["colors"].__len__()):
            informacoesLista.append([
                informacoes["colors"][i][0],
                informacoes["colors"][i][1],
                informacoes["colors"][i][2],
                i+1,
                informacoes["tissue"][i]

            ])
        # Prevent the error throwed by convert a empty array to an array
        if(not np.array_equal(segmentedMask, [])):
                file_number = 1

                # Converts the mask 3d to an image
                filename = path.basename(fileName_global).split(".")[0]
                csvName = ""
                # Chooses the correct name(according with the existing, adding
                # +1 to the number identify if this filename already exists)
                if(path.exists(f'{filename}.csv')):
                    while(path.exists(f'{filename}({str(file_number)}).csv')):
                        file_number +=1

                    csvName = f'{filename}({str(file_number)}).csv'
                else:
                    csvName = f'{filename}.csv'
                np.savetxt(csvName, segmentedMask, fmt='%d', delimiter=',')  
                f = open(csvName, "ab")
                np.savetxt(f, np.array(informacoesLista), fmt='%d', newline=' ', delimiter=',')
                f.close()
    # Rollbacks a state of the paint, copying the saved mask to the mask3d
    # deleting the copied and updating the view to the new mask with rollback
    def back_paint(self):
        global previous_paints 
        global mask3d
        global previous_segments
        global segmentedMask
        global segments_global
        # Checks if have backups of masks 3d to rollback
        if(previous_paints.__len__() >= 1):  
            # Copy the backup mask to the mask3d variable
            mask3d = copy.deepcopy(previous_paints[(previous_paints.__len__()-1)])
            # Delete the rollbacked mask
            previous_paints.__delitem__(previous_paints.__len__() -1)
            lastIndex = previous_segments["superpixel"].__len__()-1
            segmentedMask[segments_global == previous_segments["superpixel"][lastIndex]] = previous_segments["previous_identifier"][lastIndex]
            previous_segments["superpixel"].__delitem__(lastIndex)
            previous_segments["previous_identifier"].__delitem__(lastIndex)
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
        global masks_empty
        global dicom_image_array
        global segments_global
        if (not masks_empty):
            # Clear previous views
            self.axes.clear()
            # Shows the new view
            self.axes.imshow(mark_boundaries(mask3d, segments_global))
            self.view.draw()
        else:
            self.axes.clear()
            self.axes.imshow(dicom_image_array, cmap='gray')
            self.view.draw()
    def showSavedMask(self):
        self.axes.clear()
        self.axes.imshow(mask3d)
        self.view.draw()
    # Self explanatory
    def ClearView(self):
        self.axes.clear()
    # Apply the superpixel segmentation to the current dicom image array
    def SuperPixel(self):
        global dicom_image_array
        global fileName_global
        global segments_global
        global superpixel_auth
        global numSegments
        global mask3d
        sigma_slic = 1
        compactness = 0.05
        method = 'gaussian'
        # apply SLIC and extract (approximately) the supplied number of segments
        segments_global = slic(dicom_image_array, n_segments=numSegments, sigma=sigma_slic, \
                        multichannel=False, compactness=compactness, start_label=1)
        self.axes.clear()
        if(not np.array_equal(mask3d, [])):
                    self.axes.imshow(mark_boundaries(mask3d, segments_global))
        else:
            self.axes.imshow(mark_boundaries(dicom_image_array, segments_global))
        self.view.draw()
        superpixel_auth = True


# Class that create the Pallete of collors to choose for paint
class QPaletteButton(QPushButton):

    def __init__(self, color):
        super().__init__()
        self.setFixedSize(QtCore.QSize(24,24))
        self.color = color
        self.setStyleSheet("background-color: %s;" % color)

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
        global superpixel_auth
        # Just executes the method if exists an opened image
        if fileName_global != '':
            # Method that makes the CLAHE
            dicom_image_array = exposure.equalize_adapthist(dicom_image_array, clip_limit=0.03) 
            self.axes.clear()
            self.axes.imshow(dicom_image_array, cmap='gray')
            self.view.draw()
            superpixel_auth = False
    
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
        # Put yellow as default color to paint
        self.set_color(Qt.yellow)

        # self.plotwidget_original = PlotWidgetOriginal()

        # Store the instanced object of the widget modified class
        self.plotwidget_modify = PlotWidgetModify()
        
        # Store the instanced object of the painted mask class
        self.plotsuperpixelmask = PlotSuperPixelMask()   
        self.layout = QHBoxLayout()
        layout2 = QVBoxLayout()
        layout3 = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)

        # layout2.addWidget(self.plotwidget_original)

        # Shows the painted mask instanced class in the app layout
        layout2.addWidget(self.plotsuperpixelmask)

        self.layout.addLayout(layout2)

        # Shows the widget modified class in the app layout
        layout3.addWidget(self.plotwidget_modify)

        self.layout.addLayout(layout3)
        # self.layout.addWidget(self.imageLabel)

        palette = QHBoxLayout()
        self.add_palette_buttons(palette)

        # Shows the main layout, that contains the other 2(superpixel 
        # and modified)
        main_widget = QWidget()
        main_widget.setLayout(self.layout)
        self.setCentralWidget(main_widget)

        ###################################
        # palette = main_widget.QHBoxLayout()
        # self.add_palette_buttons(palette)
        # self.layout.addLayout(palette)
        
        self.createActions()
        self.createMenus()

        # Create the size of the layout
        self.setGeometry(250, 100, 1000, 600)
        self.setWindowTitle("- LAMAC -")

    @Slot()
    def on_color_clicked(self, layout):
        """When a color is changed, this function is activated and 
        changes the 'colorvec' global variable that stores the current
        color for paint"""
        global informacoes
        global currentTissue
        global masks
        global segmentedMask
        color = QColorDialog.getColor(Qt.black, self)
        qcolor = QColor(color)
        if qcolor.red() != 0 or qcolor.green() != 0 or qcolor.blue() != 0:
            # Put the RGB colors in the 'colorvec' global variable
            selectedColor= np.array([qcolor.red(), qcolor.green(), qcolor.blue()])
            verif = False
            index = 0
            for i in range(informacoes["colors"].__len__()):
                if(np.array_equal(informacoes["colors"][i], selectedColor)):
                    verif = True
                    index = i
            if(verif):
                currentTissue = index + 1
                self.set_color(color)
            else:
                item, ok = QInputDialog.getItem(self, "Select the region to paint", "List of regions", ("Fat", "Bone", "Muscle"), 0, False)
                if(ok):
                    self.set_color(color)
                    if(informacoes["tissue"].count(dictTissues[item])>0):
                        currentTissue = informacoes["tissue"].index(dictTissues[item]) + 1
                        informacoes["colors"][currentTissue-1] = selectedColor
                        if(not np.array_equal(mask3d, [])):
                            masks = np.zeros_like(dicom_image_array, dtype="bool")
                            masks[segmentedMask == currentTissue] = 1
                            # show the masked region
                            ## D_I_A = ((255 * dicom_image_array) * (~masks)).astype('uint8') 

                            mask3d[:,:,0] = informacoes['colors'][currentTissue -1][0] * masks + mask3d[:,:,0]*(~masks).astype('uint8')
                            mask3d[:,:,1] = informacoes['colors'][currentTissue -1][1] * masks + mask3d[:,:,1]*(~masks).astype('uint8')
                            mask3d[:,:,2] = informacoes['colors'][currentTissue -1][2] * masks + mask3d[:,:,2]*(~masks).astype('uint8')
                            self.plotsuperpixelmask.UpdateView()
                            
                    else:
                        size = informacoes["colors"].__len__()
                        informacoes["colors"].append(selectedColor)
                        informacoes["identifier"].append(size+1)
                        informacoes["tissue"].append(dictTissues[item])            
                        currentTissue = size+1  

    def set_color(self, color: QColor = Qt.black):
        """ Changes the color icon for the selected """
        pix_icon = QPixmap(20, 20)
        pix_icon.fill(color)

        self.color_action.setIcon(QIcon(pix_icon))
        # self.imageLabel.set_pen_color(color)
        # self.color_action.setText(QColor(color).name())

    def add_palette_buttons(self, layout):
        for c in COLORS:
            b = QPaletteButton(c)
            b.pressed.connect(lambda c=c: self.canvas.set_pen_color(c))
    def recoveryMask3d(self):
        global mask3d
        global informacoes
        global segmentedMask
        global masks
        masks = np.zeros_like(segmentedMask, dtype="bool")
        
        mask3d = np.zeros((segmentedMask.shape[0],segmentedMask.shape[1],3), dtype = "uint8")
        for i in range(informacoes["tissue"].__len__()):
            masks = np.zeros_like(segmentedMask, dtype="bool")
            masks[segmentedMask == informacoes["tissue"][i]] = 1
            mask3d[:,:,0] = informacoes['colors'][i][0] * masks + mask3d[:,:,0]*(~masks).astype('uint8')
            mask3d[:,:,1] = informacoes['colors'][i][1] * masks + mask3d[:,:,1]*(~masks).astype('uint8')
            mask3d[:,:,2] = informacoes['colors'][i][2] * masks + mask3d[:,:,2]*(~masks).astype('uint8')
        self.plotsuperpixelmask.showSavedMask()
        
        
    def open(self):
        """Open the interface to choose the file to display in the app"""
        global fileName_global
        global dicom_image_array
        global mask3d
        global masks_empty
        global currentTissue
        global informacoes
        global dictTissues
        global segmentedMask
        fileName_global = self.pathFile()
        if(fileName_global.split(".")[1] == "csv"):
            file = open(fileName_global)
            lines = file.readlines()
            informacoesStr = lines[lines.__len__()-1].split(" ")[:-1]
            for i in range(informacoesStr.__len__()):
                informacoesStr[i] = informacoesStr[i].split(",")
            informacoesInt = np.array(informacoesStr, dtype=int)
            informacoes = {"colors":[], "identifier":[], "tissue":[]}
            for i in range(informacoesInt.__len__()):
                informacoes["colors"].append(np.array([informacoesInt[i][0], informacoesInt[i][1], informacoesInt[i][2]]))
                informacoes["identifier"].append(informacoesInt[i][3])
                informacoes["tissue"].append(informacoesInt[i][4])
            tempMask = []
            for i in range(lines.__len__()-1):
                tempMask.append(np.array(lines[i].split(","), dtype=int))
            segmentedMask = np.array(tempMask, dtype=int)
            self.recoveryMask3d()
            file.close()
        else:
            dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
            dicom_image_array =  ConvertToUint8(dicom_image_array)
            # self.plotwidget_original.on_change()
            self.plotwidget_modify.on_change()
            imageViewer.plotsuperpixelmask.UpdateView()
            mask3d = []
            masks_empty = True
            currentTissue = 0
            segmentedMask = []
            informacoes = {"colors":[], "identifier":[], "tissue":[]}
            item, ok = QInputDialog.getItem(self, "Select the region to paint", "List of regions", ("Fat", "Bone", "Muscle"), 0, False)
            while not ok:
                item, ok = QInputDialog.getItem(self, "Select the region to paint", "List of regions", ("Fat", "Bone", "Muscle"), 0, False)
            informacoes["colors"].append(np.array([255, 255, 0]))
            informacoes["identifier"].append(1)
            informacoes["tissue"].append(dictTissues[item]) 
            currentTissue = 1
            self.set_color(Qt.yellow)
    def pathFile(self):
        """Get the path of the selected file"""
        fileName_global, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                         QDir.currentPath(), filter="DICOM (*.dcm *.);;csv(*.csv)")
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

    #Follow methods are self explanatory
    def HistMethodCLAHE(self):
        global dicom_image_array
        if not np.array_equal(dicom_image_array, []):
            # self.plotwidget_original.HistMethodClahe()
            self.plotwidget_modify.HistMethodClahe()
            self.plotsuperpixelmask.UpdateView()
    
    def SuperPixel(self):
        global dicom_image_array
        # self.plotwidget_original.SuperPixel()
        if not np.array_equal(dicom_image_array, []):
            self.plotsuperpixelmask.SuperPixel()
    def OriginalImage(self):
        global fileName_global
        # self.plotwidget_original.ResetDicom()
        if fileName_global != '':
            self.plotwidget_modify.ResetDicom()
            self.plotsuperpixelmask.UpdateView()
    def RemoveObjects(self):
        global dicom_image_array
        # self.plotwidget_original.DeleteObjects()
        if not np.array_equal(dicom_image_array, []):
            self.plotwidget_modify.DeleteObjects()
            self.plotsuperpixelmask.UpdateView()     
    def about(self):
        QMessageBox.about(self, "LAMAC",
                          "<p>Segmentador Manual !!! </p>")

    def the_button_was_clicked(self):
        self.SuperPixel()

    def changeNumSegments(self):
        global numSegments
        superpixelsNumber, ok = QInputDialog.getInt(self, "Número de SuperPixels",
                                "SuperPixels", QLineEdit.Normal)
        if(ok):
            numSegments = superpixelsNumber
    def resetMask3d(self):
        global mask3d
        global previous_paints
        global masks_empty
        if(not np.array_equal(dicom_image_array, [])):
            previous_paints = []
            mask3d = np.zeros((dicom_image_array.shape[0],dicom_image_array.shape[1],3), dtype = "uint8")
            mask3d[:,:,0] = 255 * dicom_image_array 
            mask3d[:,:,1] = 255 * dicom_image_array 
            mask3d[:,:,2] = 255 * dicom_image_array
            masks_empty = False
            previous_paints.append(copy.deepcopy(mask3d))
            imageViewer.plotsuperpixelmask.UpdateView()
        
    def createActions(self):
        """Create the actions to put in menu options"""
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
        self.changeNumSegmentsAct = QtGui.QAction("&Change amount of superpixels", self, shortcut="Ctrl+1",
                                     triggered=self.changeNumSegments)

    def createMenus(self):
        """Put the created actions in a menu"""
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
        self.viewMenu.addSeparator()
        self.viewMenu.addAction(self.SuperPixelAct)
        
        self.viewMenu.addAction(self.changeNumSegmentsAct)
        self.viewMenu.addSeparator()
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

    # Instances the app and shows the main class
    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec())