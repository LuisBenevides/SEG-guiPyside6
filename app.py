from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
import cv2 as cv2
from matplotlib import pyplot as plt
import skimage.filters.edges
import pydicom.encoders.gdcm
import pydicom.encoders.pylibjpeg
import pydicom.pixel_data_handlers.pylibjpeg_handler
from skimage.segmentation import mark_boundaries
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvas
from functions import *
import copy
from PIL import Image
from os import path
from scipy.ndimage import binary_fill_holes
graph = ""
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
clip_limit = 0.03
sigma_slic = 1
compactness = 0.05
segmentedMask =[]
currentTissue = 0
informacoes = {"colors":[], "identifier":[], "tissue":[]}
previous_segments = {"superpixel":[], "previous_identifier":[]}
dictTissues = {"Fat":1,"Intramuscular Fat":2, "Visceral Fat":3, "Bone":4, "Muscle":5, "Organ":6, "Other": 7}
currentPlot = 0
csvFlag = False
# Click event for paint superpixel
def mouse_event(event):
    global segments_global
    global superpixel_auth
    if ((event.xdata != None or event.ydata != None) 
    and ((event.xdata > 1 and event.ydata >1)) 
    and (superpixel_auth == True) 
    and (
        (
        (str(imageViewer.plotsuperpixelmask.toolbar._actions["zoom"]).__contains__("checked=false"))
        and (str(imageViewer.plotsuperpixelmask.toolbar._actions["pan"]).__contains__("checked=false"))
        and currentPlot == 0
        )
    or 
        (
        (str(imageViewer.plotwidget_modify.toolbar._actions["zoom"]).__contains__("checked=false"))
        and (str(imageViewer.plotwidget_modify.toolbar._actions["pan"]).__contains__("checked=false"))
        and currentPlot == 1
        ))
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
class PercentagesGraph(QWidget):
    def __init__(self):
        super().__init__()
        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        self.axes.set_title("Porcentagens")
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.view)
        self.setLayout(vlayout) 
    def calculatePercentages(self):
        global segmentedMask
        global mask3d
        global informacoes
        global dictTissues
        if(not (np.array_equal(mask3d, []) 
        or np.array_equal(segmentedMask, []))):
            totalpixels = np.count_nonzero((binary_fill_holes(segmentedMask)))
            labels = []
            sizes = []
            listKeys = list(dictTissues.keys())
            listValues = list(dictTissues.values())
            for i in range(informacoes["tissue"].__len__()):
                tissue = informacoes["tissue"][i]
                identifier = informacoes["identifier"][i]
                labels.append(listKeys[listValues.index(tissue)])
                pixels = np.count_nonzero(segmentedMask == identifier)
                totalpixels = totalpixels - pixels
                sizes.append(pixels)
            sizes.append(totalpixels)
            labels.append("Others")
            self.axes.pie(sizes, labels=labels, autopct='%1.1f%%',
            shadow=True, startangle=90)
            self.axes.axis('equal')
class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        global numSegments
        global sigma_slic
        global compactness
        global clip_limit
        self.setWindowTitle("Parâmetros")
        self.label1 = QLabel("Superpixels")
        self.input1 = QLineEdit(str(numSegments))
        self.input1.setValidator(QIntValidator(1000, 10000))
        self.label2 = QLabel("Clip limit(CLAHE)") 
        self.input2 = QDoubleSpinBox()
        self.input2.setValue(clip_limit)
        self.input2.setMaximum(10)
        self.label3 = QLabel("sigma")
        self.input3 = QLineEdit(str(sigma_slic))
        self.input3.setValidator(QIntValidator(0, 10))
        self.label4 = QLabel("Compactness")
        self.input4 = QDoubleSpinBox()
        self.input4.setValue(compactness)
        self.input4.setMaximum(10)
        self.button = QPushButton("Ok")
        QBtn = QDialogButtonBox.Yes | QDialogButtonBox.No
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        layout1 = QHBoxLayout()
        layout1.addWidget(self.label1)
        layout1.addWidget(self.input1)
        layout2 = QHBoxLayout()
        layout2.addWidget(self.label2)
        layout2.addWidget(self.input2)
        layout3 = QHBoxLayout()
        layout3.addWidget(self.label3)
        layout3.addWidget(self.input3)
        layout4 = QHBoxLayout()
        layout4.addWidget(self.label4)
        layout4.addWidget(self.input4)
        layout = QVBoxLayout()
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        layout.addLayout(layout3)
        layout.addLayout(layout4)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
    def accept(self):
        global numSegments
        global sigma_slic
        global compactness
        global clip_limit
        numSegments = int(self.input1.text())
        clip_limit = float(self.input2.text().replace(",", "."))
        sigma_slic = int(self.input3.text())
        compactness = float(self.input4.text().replace(",", "."))
        self.close()
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
            if(np.array_equal(segments_global, []) and not np.array_equal(mask3d, [])):
                imageViewer.plotsuperpixelmask.showSavedMask()
            else:
                imageViewer.plotsuperpixelmask.UpdateView()

# Class that shows the painted image
class PlotSuperPixelMask(QWidget):
    def __init__(self):
        super().__init__()
        self.view = FigureCanvas(Figure(figsize=(5, 3)))
        self.axes = self.view.figure.subplots()
        self.axes.set_title("Máscara/SuperPixel")
        # Includes the toolbar
        self.toolbar = MplToolbar(self.view, self)
        # Create the event associated with a function on click
        self.view.mpl_connect('button_press_event', self.callMouseEvent)
        self.im = ""
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout) 
    # Update the view, displaying the mask3d(if modified, shows the new mask)
    def callMouseEvent(self, event):
        global currentPlot
        currentPlot = 0
        mouse_event(event)
    def UpdateView(self):
        global mask3d
        global masks_empty
        global dicom_image_array
        global segments_global
        if (not masks_empty):
            if(self.im == ""):
                # Clear previous views
                self.axes.clear()
                # Shows the new view
                self.im = self.axes.imshow(mark_boundaries(mask3d, segments_global))
                self.view.draw()
            else:
                self.im.set_clim([0, 255])
                self.im.set_data(mark_boundaries(mask3d, segments_global))
                self.view.draw()
        else:
            if(self.im == ""):
                self.axes.clear()
                self.im = self.axes.imshow(dicom_image_array, cmap='gray')
                self.view.draw()
            else:
                self.im.set_data(dicom_image_array)
                self.im.set_clim([dicom_image_array.min(), dicom_image_array.max()])
                self.view.draw()
    def showSavedMask(self):
        self.axes.clear()
        self.im = self.axes.imshow(mask3d)
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
        global sigma_slic
        global compactness
        # apply SLIC and extract (approximately) the supplied number of segments
        segments_global = slic(dicom_image_array, n_segments=numSegments, sigma=sigma_slic, \
                        multichannel=False, compactness=compactness, start_label=1)
        self.axes.clear()
        if(not np.array_equal(mask3d, [])):
                self.im = self.axes.imshow(mark_boundaries(mask3d, segments_global))
        else:
                self.im = self.axes.imshow(mark_boundaries(dicom_image_array, segments_global))
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
        self.axes.set_title("Imagem Conferência")
        self.toolbar = MplToolbar(self.view, self)
        self.view.mpl_connect('button_press_event', self.callMouseEvent)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.toolbar)
        vlayout.addWidget(self.view)
        self.setLayout(vlayout)

        # self.on_change()
    def callMouseEvent(self, event):
        global currentPlot
        currentPlot = 1
        mouse_event(event)
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
            global clip_limit
            dicom_image_array = exposure.equalize_adapthist(dicom_image_array, clip_limit=clip_limit) 
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
        self.setWindowTitle("LAMAC")
        self.setWindowIcon(QPixmap("./icon.png"))

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
                item, ok = QInputDialog.getItem(self, "Select the region to paint", "List of regions", ("Fat","Intramuscular Fat", "Visceral Fat", "Bone", "Muscle", "Organ", "Other"), 0, False)
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
            masks[segmentedMask == informacoes["identifier"][i]] = 1
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
        global csvFlag
        global segments_global
        global superpixel_auth
        global previous_paints
        global previous_segments
        previous_segments = {"superpixel":[], "previous_identifier":[]}
        previous_paints = []
        superpixel_auth = False
        fileName_global = self.pathFile()
        if(fileName_global):
            if(fileName_global.split(".")[1] == "csv"):
                csvFlag = True
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
                self.plotwidget_modify.axes.clear()
                self.plotwidget_modify.view.draw()
                dicom_image_array = []
            else:
                dicom_image_array = dicom2array(pydicom.dcmread(fileName_global, force=True))
                dicom_image_array =  ConvertToUint8(dicom_image_array)
                # self.plotwidget_original.on_change()
                self.plotwidget_modify.on_change()
                ok = 0
                if(csvFlag):
                    confirmDialog = CustomDialog()
                    ok = confirmDialog.show()
                if(ok):  
                    currentTissue = 1
                    self.set_color(QColor(informacoes["colors"][0][0], informacoes["colors"][0][1], informacoes["colors"][0][2]))
                    segments_global = []
                    masks_empty = False
                else:
                    mask3d = []
                    masks_empty = True
                    currentTissue = 0
                    segmentedMask = []
                    segments_global = []
                    informacoes = {"colors":[], "identifier":[], "tissue":[]}
                    item, ok = QInputDialog.getItem(self, "Select the region to paint", "List of regions", ("Fat","Intramuscular Fat", "Visceral Fat", "Bone", "Muscle", "Organ", "Other"), 0, False)
                    while not ok:
                        item, ok = QInputDialog.getItem(self, "Select the region to paint", "List of regions", ("Fat","Intramuscular Fat", "Visceral Fat", "Bone", "Muscle", "Organ", "Other"), 0, False)
                    informacoes["colors"].append(np.array([255, 255, 0]))
                    informacoes["identifier"].append(1)
                    informacoes["tissue"].append(dictTissues[item]) 
                    currentTissue = 1
                    self.set_color(Qt.yellow)
                    imageViewer.plotsuperpixelmask.UpdateView()
                csvFlag = False
    def pathFile(self):
        """Get the path of the selected file"""
        fileName_global, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                         QDir.currentPath(), filter="DICOM (*.dcm *.);;csv(*.csv)")
        return fileName_global


    #Follow methods are self explanatory
    def HistMethodCLAHE(self):
        global dicom_image_array
        global segments_global
        global mask3d
        if not np.array_equal(dicom_image_array, []):
            if(masks_empty == True):
                self.plotsuperpixelmask.im = ""
            self.plotwidget_modify.HistMethodClahe()
            if(np.array_equal(segments_global, []) and not np.array_equal(mask3d, [])):
                self.plotsuperpixelmask.showSavedMask()
            else:
                self.plotsuperpixelmask.UpdateView()
    
    def SuperPixel(self):
        global dicom_image_array
        # self.plotwidget_original.SuperPixel()
        if not np.array_equal(dicom_image_array, []):
            self.plotsuperpixelmask.SuperPixel()
    def OriginalImage(self):
        global fileName_global
        global segments_global
        global mask3d
        # self.plotwidget_original.ResetDicom()
        if fileName_global != '':
            if not fileName_global.split(".")[1] == "csv":
                self.plotwidget_modify.ResetDicom()
                if(masks_empty):
                    self.plotsuperpixelmask.im = ""
                if(np.array_equal(segments_global, []) and not np.array_equal(mask3d, [])):
                    self.plotsuperpixelmask.showSavedMask()
                else:
                    self.plotsuperpixelmask.UpdateView()
    def RemoveObjects(self):
        global dicom_image_array
        global segments_global
        global mask3d
        # self.plotwidget_original.DeleteObjects()
        if not np.array_equal(dicom_image_array, []):
            if(masks_empty == True):
                self.plotsuperpixelmask.im = ""
            self.plotwidget_modify.DeleteObjects()
            if(np.array_equal(segments_global, []) and not np.array_equal(mask3d, [])):
                self.plotsuperpixelmask.showSavedMask()
            else:
                self.plotsuperpixelmask.UpdateView()    
    def about(self):
        QMessageBox.about(self, "LAMAC",
                          "<p>Segmentador Manual !!! </p>")

    def the_button_was_clicked(self):
        self.SuperPixel()

    def changeOptions(self):
        form = Form()
        form.exec()
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
    def calculatePercentages(self):
        global graph
        graph = PercentagesGraph()
        graph.calculatePercentages()
        graph.show()
    def createActions(self):
        """Create the actions to put in menu options"""
        self.openAct = QtGui.QAction("&Open...", self, shortcut="Ctrl+O",
                                     triggered=self.open)
        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                                     triggered=self.close)
        self.HistMethodCLAHEAct = QtGui.QAction("&Hist CLAHE", self, shortcut="Ctrl+C",
                                                triggered=self.HistMethodCLAHE)
        self.SuperPixelAct = QtGui.QAction("&SuperPixel", self,  shortcut="Ctrl+Shift+S",
                                           triggered=self.SuperPixel)
        self.OriginalImageAct = QtGui.QAction("&Original Image", self,
                                              triggered=self.OriginalImage)
        self.RemoveObjectsAct = QtGui.QAction("&Remove Objects", self,  shortcut="Ctrl+R",
                                              triggered=self.RemoveObjects)
        
        self.aboutAct = QtGui.QAction("&About", self, triggered=self.about)

        self.aboutQtAct = QtGui.QAction("About &Qt", self,
                                        triggered=qApp.aboutQt)
        self.saveAct = QtGui.QAction("&Save", self, shortcut="Ctrl+S",
                                     triggered=self.plotsuperpixelmask.toolbar.save_mask)
        self.backPaintAct = QtGui.QAction("&Back", self, shortcut="Ctrl+Z",
                                     triggered=self.plotsuperpixelmask.toolbar.back_paint)
        self.changeOptionsAct = QtGui.QAction("&Change Options", self,
                                     triggered=self.changeOptions)
        self.calculatePercentagesAct = QtGui.QAction("&Calculate Percentages", self,
                                     triggered=self.calculatePercentages)
    def createMenus(self):
        """Put the created actions in a menu"""
        self.fileMenu = QMenu("&File", self)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.exitAct)

        self.viewMenu = QMenu("&View", self)
        self.viewMenu.addAction(self.SuperPixelAct)
        self.viewMenu.addAction(self.HistMethodCLAHEAct)
        self.viewMenu.addAction(self.OriginalImageAct)
        self.viewMenu.addAction(self.RemoveObjectsAct)
        self.viewMenu.addAction(self.backPaintAct)
        self.viewMenu.addAction(self.calculatePercentagesAct)
        self.optionsMenu = QMenu("&Options", self)
        self.optionsMenu.addAction(self.changeOptionsAct)
        self.helpMenu = QMenu("&Help", self)
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutQtAct)

        self.menuBar().addMenu(self.fileMenu)
        self.menuBar().addMenu(self.viewMenu)
        self.menuBar().addMenu(self.optionsMenu)
        self.menuBar().addMenu(self.helpMenu)

if __name__ == '__main__':
    import sys

    # Instances the app and shows the main class
    app = QApplication(sys.argv)
    imageViewer = ImageViewer()
    imageViewer.show()
    sys.exit(app.exec())