from PySide2 import QtCore
from PySide2 import QtGui
from PySide2 import QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMayaUI as omui
import maya.OpenMaya as om

import maya.cmds as cmds
import os

###Tested in MAYA 2019 only.

def maya_main_window():

    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)


class OverwriteDialog(QtWidgets.QDialog):

    def __init__(self, parent=maya_main_window()):
        super(OverwriteDialog, self).__init__(parent)

        self.setWindowTitle("Overwrite Warning")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.warning_label = QtWidgets.QLabel("Object name already exists! Do you want to overwrite?")

        self.okay_btn = QtWidgets.QPushButton("Overwrite")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")

    def create_layout(self):
        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(self.warning_label)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addSpacing(2)
        button_layout.addWidget(self.okay_btn)
        button_layout.addWidget(self.cancel_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(label_layout)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.okay_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.close)


class ModelKitDialog(QtWidgets.QDialog):

    WINDOW_TITLE = "Model Kit"

    def __init__(self, parent=maya_main_window()):
        super(ModelKitDialog, self).__init__(parent)

        self.folder_path = None
        self.img_path = None
        self.cameraName = None
        self.filename = None

        self.setWindowTitle(self.WINDOW_TITLE)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(625)
        self.setMinimumHeight(220)
        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        self.table_wdg = QtWidgets.QTableWidget()
        self.table_wdg.setColumnCount(5)
        for each in range(0, self.table_wdg.columnCount()):
            self.table_wdg.setColumnWidth(each, 120)
        self.table_wdg.setRowCount(1)
        self.table_wdg.setRowHeight(0, 120)
        
        self.libraryload_lable = QtWidgets.QLabel("Library Folder")
        self.libraryload_le = QtWidgets.QLineEdit()
        self.select_lib_path_btn = QtWidgets.QPushButton("")
        self.select_lib_path_btn.setIcon(QtGui.QIcon(":fileOpen.png"))
        self.load_library_btn = QtWidgets.QPushButton("Load Existing")

        self.add_btn = QtWidgets.QPushButton("Add Object")
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layout(self):
        lib_loader_layout = QtWidgets.QHBoxLayout()
        lib_loader_layout.addWidget(self.libraryload_lable)
        lib_loader_layout.addWidget(self.libraryload_le)
        lib_loader_layout.addWidget(self.select_lib_path_btn)
        lib_loader_layout.addWidget(self.load_library_btn)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addSpacing(2)
        button_layout.addStretch()
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.close_btn)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(2,2,2,2)
        main_layout.addSpacing(2)
        main_layout.addLayout(lib_loader_layout)
        main_layout.addWidget(self.table_wdg)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        self.select_lib_path_btn.clicked.connect(self.show_folder_select_dialog)
        self.load_library_btn.clicked.connect(self.load_existing_library)

        self.add_btn.clicked.connect(self.export_geo)
        self.close_btn.clicked.connect(self.close)
        self.table_wdg.cellClicked.connect(self.table_cell_clicked)

    def show_folder_select_dialog(self):
        self.launch_libfolder_sel_window()
        self.img_path = os.path.join(self.folder_path, "images")
        self.img_path = os.path.normpath(self.img_path)
        isDir = os.path.isdir(self.img_path)
        if not isDir:
            os.makedirs(self.img_path)

    def load_existing_library(self):
        # select existing lib folder. If obj's exist, skip, or if not
        # check for thumbnail image and load the obj's into new cells
        file_type = "obj"
        libfolder_le_text = self.libraryload_le.text()

        if not libfolder_le_text:
            self.show_folder_select_dialog()
        else:
            files = cmds.getFileList(folder=libfolder_le_text, filespec='*.%s' % file_type)

            if len(files) == 0:          
                cmds.warning("No Files to Import")
            else:
                for f in files:
                    obj_name = os.path.splitext(f)[0]
                    self.create_filepath(obj_name)
                    obj_exists = self.check_obj_exists(self.filename)[0]
                    if not obj_exists:
                        emptyIndex = self.find_empty_cell()
                        obj_img_name = os.path.join(self.img_path, obj_name + ".jpg")
                        obj_img_name = os.path.normpath(obj_img_name)
                        img_exists = cmds.file(obj_img_name, q=True, ex=True)
                        if img_exists:
                            cropImage = self.create_img(obj_img_name)
                            self.add_cell(emptyIndex, cropImage, True)
                        else:
                            self.add_cell(emptyIndex, None, False)
                    else:
                        print("{0} ".format(obj_name) + "already exists")

    def export_geo(self):
        # Export selected object to library directory, creating thumbnail image
        # Prompt to overwrite if same name exists already.
        
        objSel = cmds.ls(sl=True)
        sel = cmds.ls(sl=True, type='transform', dag=True, ni=True)
        
        if sel:
            if self.folder_path == None:
                self.show_folder_select_dialog()
                cmds.warning("Please select folder path!")
            else:
                self.create_filepath(sel[0])
                obj_exists, index = self.check_obj_exists(self.filename)     
                if not obj_exists:
                    #center the obj to world origin so it will import without offsets
                    pos = self.center_obj(objSel[0])
                    
                    thumbnail_image = self.save_file_create_thumbnail(sel[0])
                    emptyIndex = self.find_empty_cell()
                    self.add_cell(emptyIndex, thumbnail_image, True)
                    print("Export of {0} successful in cell {1}".format(self.filename, emptyIndex))
                    
                    #return it back from wence it came
                    self.return_obj(objSel[0],pos)
                else:
                    cmds.warning("Obj Exists: {0}".format(self.filename))
                    overwrite_dialog = OverwriteDialog()
                    result = overwrite_dialog.exec_()

                    if result == QtWidgets.QDialog.Accepted:
                        pos = self.center_obj(objSel[0])
                        thumbnail_image = self.save_file_create_thumbnail(sel[0])
                        self.overwrite_cell(thumbnail_image, index)
                        self.return_obj(objSel[0],pos)

        else:
            cmds.warning("Select a mesh object to export!")

    def launch_libfolder_sel_window(self):
        self.folder_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Library Folder")
        self.libraryload_le.setText(self.folder_path)

    def overwrite_cell(self, pixmapImg, index):
        existing_cell = (self.table_wdg.item(index[0], index[1]))

        if existing_cell:
            self.set_tooltip_and_text(existing_cell)
            label = QtWidgets.QLabel()
            label.setScaledContents(True)
            label.setPixmap(pixmapImg)
            self.table_wdg.setCellWidget(index[0], index[1], label)

            print("Overwrite of {0} successful at {1}".format(self.filename, index))

    def create_filepath(self, obj_name):
        self.filename = os.path.join(self.libraryload_le.text(), obj_name + ".obj")
        self.filename = os.path.normpath(self.filename)
        
    def check_obj_exists(self, filename):
        # Comb through table to find if object name exists in a cell's text
        # If not, return 'exists', index is not relevant
        rowCount = self.table_wdg.rowCount()
        colCount = self.table_wdg.columnCount()
        for i in range(0, rowCount):
            for j in range(0, colCount):
                cellQuery = self.table_wdg.item(i,j)
                if cellQuery and cellQuery.text() == filename:
                    exists = True
                    cellIndex = (i,j)
                    return exists, cellIndex
        exists = False
        cellIndex = (0,0)
        return exists, cellIndex
    
    def center_obj(self, selection):
        #save original xform
        pos = cmds.xform(selection, query=True, worldSpace=True, translation=True)
        #create a transform at world origin to move the obj to
        temp_transform = cmds.createNode("transform")  
        cmds.matchTransform(selection, temp_transform, position=True) 
        cmds.delete(temp_transform)
        cmds.select(selection)
        return pos
    
    def return_obj(self, selection, pos):
        
        #return obj to original xform
        cmds.xform(selection, worldSpace=True, translation=(pos[0],pos[1],pos[2]))    

    def save_file_create_thumbnail(self, selection):
        cmds.file(self.filename,f=1,pr=1,typ="OBJexport",es=1,op="groups=0; ptgroups=0; materials=0; smoothing=1; normals=1")
        imageSnapshot = self.save_snapshot(selection)
        thumbnail_image = self.create_img(imageSnapshot)
        return thumbnail_image

    def create_img_cam(self):
        # Create a camera.
        self.cameraName = cmds.camera(fl=75)
        cmds.xform(self.cameraName, r=True, t=(2.6, 2.35, 3), ro=(-30.0, 40.0, 0.0))

    def return_to_perspCam(self):
        cmds.select('persp')
        perspCam = cmds.ls(sl=True)
        cmds.lookThru(perspCam)

    def save_snapshot(self, geo):
        # Create new camera, isolated selected object, frame and take snapshot
        # Delete cam and return to perspective cam
        self.create_img_cam()
        cmds.lookThru(self.cameraName)
        cmds.select(geo)

        if cmds.isolateSelect('modelPanel4', q=True, state=True):
            cmds.isolateSelect('modelPanel4', state=False)
            cmds.isolateSelect('modelPanel4', state=True)
            cmds.isolateSelect('modelPanel4', addSelected=True)
        else:
            cmds.isolateSelect('modelPanel4', state=True)
            cmds.isolateSelect('modelPanel4', addSelected=True)

        cmds.viewFit()
        imageSnapshot = (os.path.join(self.img_path, geo)) + ".jpg"
        imageSnapshot = os.path.normpath(imageSnapshot)
        cmds.refresh(cv=True, fe = "jpg", fn = imageSnapshot)
        cmds.isolateSelect('modelPanel4', state=False)
        self.return_to_perspCam()
        if self.cameraName:
            cmds.delete(self.cameraName[0])

        return imageSnapshot

    def create_img(self, img_path):
        # Create pixmap image and crop
        pixmap = QtGui.QPixmap(img_path)
        img_size = pixmap.size()
        img_width = img_size.width()
        img_height = img_size.height()

        if img_height > img_width:
            crop_height = (img_height-img_width)/2
            cropSize = QtCore.QRect(0, crop_height, img_width, img_width)
        else:
            crop_width = (img_width-img_height)/2
            cropSize = QtCore.QRect(crop_width, 0, img_height, img_height)
        
        croppedPixmap = QtGui.QPixmap.copy(pixmap, cropSize)
        return croppedPixmap

    def find_empty_cell(self):
        rowCount = self.table_wdg.rowCount()
        colCount = self.table_wdg.columnCount()

        for i in range(0, rowCount):
            for j in range(0, colCount):
                cellQuery = self.table_wdg.item(i,j)
                if not cellQuery:
                    emptyIndex = (i,j)
                    return emptyIndex
                else:
                    if i == (rowCount - 1) and j == (colCount - 1):
                        self.table_wdg.insertRow(rowCount)
                        self.table_wdg.setRowHeight(rowCount, 120)
                        emptyIndex = (rowCount, 0)
                        return emptyIndex

    def set_tooltip_and_text(self, item):
        item.setToolTip(self.filename)
        item.setText(self.filename)

    def add_cell(self, emptyIndex, pixmapImg, isNew):
        cellItem = QtWidgets.QTableWidgetItem()
        cellItem.setFlags(cellItem.flags() & ~ QtCore.Qt.ItemIsEditable)
        self.set_tooltip_and_text(cellItem)
        label = QtWidgets.QLabel()

        if not pixmapImg:
            # TODO - set a better label, option to pick image or take new one
            cellItem.setBackground(QtGui.QColor("red"))
        else:
            label.setScaledContents(True)
            label.setPixmap(pixmapImg)
        self.table_wdg.setCellWidget(emptyIndex[0], emptyIndex[1], label)
        self.table_wdg.setItem(emptyIndex[0], emptyIndex[1], cellItem)

    def get_cell_text(self, row, col):
        cellItem = self.table_wdg.item(row, col)
        if cellItem:
            cell_text = cellItem.text()
            return cell_text
        else:
            return None

    def import_object(self, obj_path):
    
        nameSpc = "ImportedObj"

        #TODO - add ability to import aligned to face selection

        if cmds.file(obj_path, q=True, ex=True):
            if not cmds.namespace( exists=nameSpc):
                cmds.namespace(add=nameSpc)
            
            cmds.namespace(set=nameSpc)
            
            #import            
            imported_objects = cmds.file(obj_path, i=True, ns="Import", rnn=True)
            #reset namespace to blank
            cmds.namespace(set=":")
            
            objName, ext = os.path.splitext(os.path.basename(obj_path))
            
            transforms = cmds.ls(imported_objects, type='transform')

            cmds.select(transforms[0], r=True)
            
            cmds.rename(transforms[0], objName)
      
        else:
            #TODO - turn into error pop-up
            cmds.warning("No files found?!?")

    def table_cell_clicked(self, *args):
        row = args[0]
        col = args[1]
        obj_path = self.get_cell_text(row, col)
        if obj_path:
            self.import_object(obj_path)
        else:
            cmds.warning("Chosen cell is empty!")


if __name__ == "__main__":

    try:
        open_import_dialog.close()
        open_import_dialog.deleteLater()
    except:
        pass

    open_import_dialog = ModelKitDialog()
    open_import_dialog.show()
