from skimage import data, img_as_float
from skimage import exposure
from skimage import color
import pydicom
import pydicom as dicom
from pydicom import dcmread
from pydicom.data import get_testdata_files
import numpy as np
from skimage.io import *
import cv2 as cv
from PIL import ImageFile
#ImageFile.LOAD_TRUNCATED_IMAGES = True
from skimage.segmentation import slic
from skimage.segmentation import mark_boundaries
from skimage.measure import label, perimeter
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
import matplotlib.backends.backend_qt5 as backend
from PySide6.QtWidgets import *
from PySide6.QtGui import *


def tissue_segmentation(hu_img, tissue):
    """Tissue segmentation

    Returns a mask of the image where the tissue was found. The tissue is a strip
    of Hounsfield Units value in the "material"'s dict
    """
    segm_img = np.zeros_like(hu_img, dtype=np.bool_)
    segm_img[ (hu_img >= materials[tissue][0][0]) &
             (hu_img <= materials[tissue][0][1]) ] = 1
    return segm_img
def select_RoI(hu_img):
    """Select Region of Interest

    Removes unwanted objects from the image, 
    such as the tomograph "bed" and sheets.
    """
    mask = np.ones_like(hu_img)
    mask[hu_img < materials['air'][0][1]] = 0
    labels = label(mask, background=0, return_num=False, connectivity=1)
    mask = np.array(labels == np.argmax(np.bincount(labels.flat)[1:]) + 1, dtype=int)
    output = np.copy(hu_img)
    output[mask==0] = np.min(hu_img)
    return output
# Colors
colors = {
    'black':  [(0,0,0),       0],
    'white':  [(255,255,255), 1],
    'red':    [(255,0,0),     2],
    'green':  [(0,255,0),     3],
    'blue':   [(0,0,255),     4],
    'yellow': [(255,255,0),   5],
    'orange': [(255,140,0),   6],
    'gray':   [(127,127,127), 9]
}
# HU range for each material
# 'material': [(minimum value, maximum value), 'color']
# Although 'muscle' minimum value should be 31 (and not -29).
# this helps in the segmentation process
materials = {
    'bone':         [(   500, 10000), 'white' ],
    'bonelike':     [(   160, 10000), 'white' ],
    'muscle':       [(   -29,   150), 'orange'], #'muscle': [(31, 150), 'blue'],
    'skmuscle':     [(    10,    40), 'red'   ],
    'organ':        [(   -29,    30), 'green' ],
    'musclelike':   [(   -50,   150), 'orange'], # includes part of subcutaneous fat
    'fat':          [(  -190,   -30), 'yellow'], 
    'scfat':        [(  -190,   -30), 'blue'  ], # subcutaneous fat
    'imfat':        [(  -150,   -50), 'green' ], # visceral fat (ver e-mail da Sara)
    'fatlike':      [(  -190,   -10), 'yellow'], # fat with a bit of muscle
    'air':          [(-10000,  -300), 'black' ]

}
def dicom2array(dcm):
    img_raw = np.float64(dcm.pixel_array)
    output = np.array( dcm.RescaleSlope * img_raw + dcm.RescaleIntercept, dtype=int )
    return output
def ConvertToUint8(dicom_image_array):
    orig_min = dicom_image_array.min()
    orig_max = dicom_image_array.max()
    target_min = 0.0
    target_max = 255.0
    dicom_image_array = (dicom_image_array-orig_min)*((target_max- 
    target_min)/(orig_max-orig_min))+target_min
    dicom_image_array = dicom_image_array.astype(np.uint8)
    return dicom_image_array
class CustomDialog(QDialog):
    def __init__(self):
        super().__init__()

        QBtn = QDialogButtonBox.Yes | QDialogButtonBox.No
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("LAMAC")
        self.setWindowIcon(QPixmap("./icon.png"))
        self.layout = QVBoxLayout()
        message = QLabel("<center>Deseja aproveitar a mascara</center> \n<center>do arquivo .csv atual?</center>")
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
    def show(self):
        return self.exec_()