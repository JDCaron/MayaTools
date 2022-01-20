from PySide2 import QtGui, QtCore, QtWidgets
from shiboken2 import wrapInstance

import maya.OpenMaya as om
import maya.OpenMayaUI as omui

from pymel.core import *
import maya.mel as mel


def maya_main_window():

    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(long(main_window_ptr), QtWidgets.QWidget)

class FloatEdit(QtWidgets.QLineEdit):
    
    valueSet = QtCore.Signal(float)

    def __init__(self, text, setFixed=False, width=0, alignment=QtCore.Qt.AlignRight, parent=None):
        super(FloatEdit, self).__init__(parent)
        self.setAlignment(alignment)
        if(setFixed):
            self.setFixedWidth(width)
        self.validator = QtGui.QDoubleValidator()
        self.setText(text)
        self.setValidator(self.validator)
        self._value = self.value()
        self.returnPressed.connect(self.apply)

    def apply(self):
        if self._value != self.value():
            self.valueSet.emit(self.value())
        self._value = self.value()

    def value(self):
        if self.text() == '':
            return None
        return float(self.text().replace(',', '.'))


class AnimationExporter(QtWidgets.QDialog):

    clipName = ""
    
    @classmethod
    def show_dialog(cls):
        if not cls.animExp:
            cls.animExp = AnimationExporter()
            
        if cls.animExp.isHidden():
            cls.animExp.show()
        else:
            cls.animExp.raise_()
            cls.animExp.activateWindow()

    def __init__(self, parent=maya_main_window()):
        super(AnimationExporter, self).__init__(parent)

        minWidth = 650
        minHeight = 500

        self.setWindowTitle("Animation Exporter")
        self.setMinimumSize(minWidth, minHeight)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setProperty("saveWindowPref", True)

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        
        self.title_frm = QtWidgets.QFrame()
        self.title_frm.setFrameShape(QtWidgets.QFrame.HLine)
        self.title_frm.setFrameShadow(QtWidgets.QFrame.Plain)
        self.title_frm.setLineWidth(5)
        
        self.title_lbl = QtWidgets.QLabel("ANIMATION CLIP EXPORTER")
        self.title_lbl.setStyleSheet("font: 24pt \"Futura\";")
        self.title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        
        self.xform_bn_lbl = QtWidgets.QLabel("Root Bone Name:")
        self.xform_bn_lbl.setMinimumWidth(120)
        self.xform_bn_le = QtWidgets.QLineEdit()
        
        self.pln_bn_chk = QtWidgets.QCheckBox('Has "Plane Bone"')
        self.pln_bn_chk.setChecked(True)
        self.pln_bn_lbl = QtWidgets.QLabel("Plane Bone Name:")
        self.pln_bn_lbl.setMinimumWidth(120)
        self.pln_bn_le = QtWidgets.QLineEdit()
        
        self.offset_lbl = QtWidgets.QLabel("Offset:")
        self.offset_lbl.setMinimumWidth(40)
        self.x = FloatEdit("0")
        self.y = FloatEdit("0")
        self.z = FloatEdit("0")
        self.offset_ex_label = QtWidgets.QLabel(" (XYZ)")
        
        self.scale_lbl = QtWidgets.QLabel("Scale:")
        self.scale_lbl.setMinimumWidth(40)
        self.scale_x = FloatEdit("1")
        self.scale_y = FloatEdit("1")
        self.scale_z = FloatEdit("1")
        self.scale_ex_lbl = QtWidgets.QLabel(" (XYZ)")
        
        self.btn_grp_frm = QtWidgets.QFrame()
        self.btn_grp_frm.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.btn_grp_frm.setFrameShadow(QtWidgets.QFrame.Plain)
        self.btn_grp_frm.setLineWidth(3)
        
        self.importRef_btn = QtWidgets.QPushButton("Import Reference")
        self.del_ns_chk = QtWidgets.QCheckBox("Delete Reference Namespaces")
        self.del_ns_chk.setChecked(True)
        self.del_ns_btn = QtWidgets.QPushButton("Remove Namespaces")
        self.bakeAnim_btn = QtWidgets.QPushButton("Bake Animation")
        self.delConts_btn = QtWidgets.QPushButton("Delete Constraints")
        self.setXform_btn = QtWidgets.QPushButton("Set Offset and Scale")
                
        self.SavMult_radbtn = QtWidgets.QRadioButton("Save Multiple Clips")
        self.SavSngl_radbtn = QtWidgets.QRadioButton("Save Clips to Single File")
        self.rad_btn_grp = QtWidgets.QButtonGroup()
        self.rad_btn_grp.addButton(self.SavMult_radbtn)
        self.rad_btn_grp.addButton(self.SavSngl_radbtn)
        self.rad_btn_spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        
        self.clip_title_lbl = QtWidgets.QLabel("Clip Name")
        self.clip_title_lbl.setAlignment(QtCore.Qt.AlignCenter)
        self.clip_title_start_lbl = QtWidgets.QLabel("Start")
        self.clip_title_start_lbl.setFixedWidth(35)
        self.clip_title_end_lbl = QtWidgets.QLabel("End")
        self.clip_title_end_lbl.setFixedWidth(35)
        self.clip_title_spacer = QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        
        self.clipName_le = QtWidgets.QLineEdit("Clip Name:")
        
        self.addRow_le = QtWidgets.QLineEdit("Add New Clip >>>")
        self.addRow_le.setEnabled(False)                       
        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Base,QtCore.Qt.darkGray)
        palette.setColor(QtGui.QPalette.Text,QtCore.Qt.black)
        self.addRow_le.setPalette(palette)
        
        self.addRow_btn = QtWidgets.QPushButton()
        self.addRow_btn.setIcon(QtGui.QIcon(":addClip.png"))
        self.addRow_btn.setMaximumWidth(35)
        
        self.filepath_le = QtWidgets.QLineEdit()
        self.filepath_le.setPlaceholderText("Export Path")
        self.filepath_btn = QtWidgets.QPushButton();
        self.filepath_btn.setIcon(QtGui.QIcon(":SP_DirIcon.png"))
        self.filepath_btn.setToolTip("Select export folder")   
        
        self.filename_lbl = QtWidgets.QLabel("File Name:")
        self.filename_le = QtWidgets.QLineEdit()

        self.export_btn = QtWidgets.QPushButton("Export")
        
    def create_connections(self):
        
        self.setXform_btn.clicked.connect(self.setOffsetAndScale)
        self.importRef_btn.clicked.connect(self.importReferences)
        self.del_ns_btn.clicked.connect(self.deleteNamespaces)
        self.bakeAnim_btn.clicked.connect(self.bakeKeys)
        self.delConts_btn.clicked.connect(self.delConstraints)
        
        self.SavMult_radbtn.clicked.connect(self.saveOptionsRadioBtnToggled)
        self.SavSngl_radbtn.clicked.connect(self.saveOptionsRadioBtnToggled)

        self.filepath_btn.clicked.connect(self.getFolderPath)
        
        self.addRow_btn.clicked.connect(lambda: self.addClipRow(self.clip_main_layout))
        
        self.export_btn.clicked.connect(self.startExport)

    def create_layout(self):
        
        title_layout = QtWidgets.QVBoxLayout()
        title_layout.addWidget(self.title_lbl)
        self.title_frm.setLayout(title_layout)
        
        xfrom_bn_layout = QtWidgets.QHBoxLayout()
        xfrom_bn_layout.addWidget(self.xform_bn_lbl)
        xfrom_bn_layout.addWidget(self.xform_bn_le)
        self.xform_bn_le.setPlaceholderText("Transform_Bn")
        
        pln_bn_layout = QtWidgets.QHBoxLayout()
        pln_bn_layout.addWidget(self.pln_bn_lbl)
        pln_bn_layout.addWidget(self.pln_bn_le)
        pln_bn_layout.addWidget(self.pln_bn_chk)
        self.pln_bn_le.setPlaceholderText("Plane_Bn")

        self.offset_layout = QtWidgets.QHBoxLayout()
        self.offset_layout.addWidget(self.offset_lbl)
        self.offset_layout.addWidget(self.x)
        self.offset_layout.addWidget(self.y)
        self.offset_layout.addWidget(self.z)
        self.offset_layout.addWidget(self.offset_ex_label)
        
        self.scale_layout = QtWidgets.QHBoxLayout()
        self.scale_layout.addWidget(self.scale_lbl)
        self.scale_layout.addWidget(self.scale_x)
        self.scale_layout.addWidget(self.scale_y)
        self.scale_layout.addWidget(self.scale_z)
        self.scale_layout.addWidget(self.scale_ex_lbl)
        
        btn_layout = QtWidgets.QVBoxLayout()
        btn_layout.addWidget(self.importRef_btn)
        btn_layout.addWidget(self.del_ns_chk)
        btn_layout.addWidget(self.del_ns_btn)
        btn_layout.addWidget(self.bakeAnim_btn)
        btn_layout.addWidget(self.delConts_btn)
        btn_layout.addWidget(self.setXform_btn)
        self.btn_grp_frm.setLayout(btn_layout)
        
        save_radio_btn_layout = QtWidgets.QHBoxLayout()
        save_radio_btn_layout.addWidget(self.SavMult_radbtn)
        save_radio_btn_layout.addWidget(self.SavSngl_radbtn)        
        self.SavSngl_radbtn.setChecked(True)
        save_radio_btn_layout.addSpacerItem(self.rad_btn_spacer)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.export_btn)            
        
        clip_title_layout = QtWidgets.QHBoxLayout()
        clip_title_layout.addWidget(self.clip_title_lbl)
        clip_title_layout.addWidget(self.clip_title_start_lbl)
        clip_title_layout.addWidget(self.clip_title_end_lbl)
        clip_title_layout.addSpacerItem(self.clip_title_spacer)
        
        clip_remove_layout = QtWidgets.QHBoxLayout()
        clip_remove_layout.addWidget(self.addRow_le)
        clip_remove_layout.addWidget(self.addRow_btn)
        clip_remove_layout.setAlignment(QtCore.Qt.AlignRight|QtCore.Qt.AlignTop)
        
        self.clip_main_layout = QtWidgets.QVBoxLayout()
        self.clip_main_layout.addLayout(clip_remove_layout)
             
        new_clip_area = QtWidgets.QWidget()
        new_clip_area.setLayout(self.clip_main_layout)
        
        clip_scroll_area = QtWidgets.QScrollArea()
        clip_scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        clip_scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        clip_scroll_area.setWidgetResizable(True)
        clip_scroll_area.setWidget(new_clip_area)
        
        filepath_layout = QtWidgets.QHBoxLayout()
        filepath_layout.addWidget(self.filepath_le)
        filepath_layout.addWidget(self.filepath_btn)
        
        filename_layout = QtWidgets.QHBoxLayout()
        filename_layout.addWidget(self.filename_lbl)
        filename_layout.addWidget(self.filename_le)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        
        main_layout.addWidget(self.title_frm)
        
        main_layout.addLayout(xfrom_bn_layout)
        main_layout.addLayout(pln_bn_layout)
        main_layout.addLayout(self.offset_layout)
        main_layout.addLayout(self.scale_layout)
        
        main_layout.addWidget(self.btn_grp_frm)
        
        main_layout.addLayout(save_radio_btn_layout)
        main_layout.addLayout(clip_title_layout)
        
        main_layout.addWidget(clip_scroll_area)
        
        main_layout.addLayout(filepath_layout)
        main_layout.addLayout(filename_layout)
        main_layout.addLayout(button_layout)
    
    def addClipRow(self, layout):
      
        index = layout.count() - 1
        timeline = self.getTimelineMinMax()

        self.delClip_btn = QtWidgets.QPushButton()
        self.delClip_btn.setIcon(QtGui.QIcon(":deleteClip.png"))
        self.clip_name_le = QtWidgets.QLineEdit()
        self.clip_name_le.setPlaceholderText("Enter Clip Name")
        self.start_frame_le = FloatEdit(str(timeline[0]), True, 35)
        self.stop_frame_le = FloatEdit(str(timeline[1]), True, 35)
        
        clip_layout = QtWidgets.QHBoxLayout()
        clip_layout.addWidget(self.delClip_btn)
        clip_layout.addWidget(self.clip_name_le)
        clip_layout.addWidget(self.start_frame_le)
        clip_layout.addWidget(self.stop_frame_le)
        
        self.delClip_btn.clicked.connect(lambda: self.removeClipRow(clip_layout))
        
        layout.insertLayout(index, clip_layout)
        
    def removeClipRow(self, layout):
        
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None: 
                    widget.setParent(None)
                else:
                    self.removeClipRow(item.layout())
    
    def checkObjExists(self, obj):
        if objExists(obj):
            select(obj, r=True)
            return True
        else:
            self.genericWarning("%s not found, please set correct bone name" % obj)
            return False
    
    def getTransformBone(self):
        
        if self.xform_bn_le.text() != "":
            transformBone = self.xform_bn_le.text()
        else:
            transformBone = self.xform_bn_le.placeholderText()
        
        return self.checkObjExists(transformBone)
        
    def getPlaneBone(self):
        
        if self.pln_bn_le.text() != "":
            planeBone = self.pln_bn_le.text()
        else:
            planeBone = self.pln_bn_le.placeholderText()
            
        return self.checkObjExists(planeBone)
        
    def getTimelineMinMax(self):
        
        minTimeline = int(playbackOptions(q=True, min=True))
        maxTimeline = int(playbackOptions(q=True, max=True))
        
        return(minTimeline, maxTimeline)
    
    def getFileName(self):
        
        if self.SavSngl_radbtn.isChecked():
            return self.filename_le.text()
        else:
            return self.filename_le.text() + self.clipName
    
    def stringify(self, x):
        
        return '"%s"' % x if str(x) == x else str(x)
    
    def saveOptionsRadioBtnToggled(self):
        if self.SavMult_radbtn.isChecked():
            self.filename_lbl.setText("File Prefix:")           
        else:
            self.filename_lbl.setText("File Name:")
            
    def importReferences(self):
        refs = listReferences() or []
        
        for ref in refs:
            if ref.isLoaded():
                if self.del_ns_chk.isChecked():
                    ref.importContents(removeNamespace=True)
                else:
                    ref.importContents()
                
    def deleteNamespaces(self):
        
        defaults = ['UI', 'shared']
        namespaces = (ns for ns in namespaceInfo(lon=True) if ns not in defaults)
        
        for ns in namespaces:
            
            namespace( removeNamespace = ns, mergeNamespaceWithParent = True)

    def bakeKeys(self):
    
        if self.getTransformBone():
        
            sel = ls( sl=True )
            timeline = self.getTimelineMinMax()
            bakeResults(sel[0], sm=True, hi="below", t=( timeline ))
        
        if self.pln_bn_chk.isChecked(): 
            if self.getPlaneBone():
                sel = ls( sl=True )
                attrs = "translate", "rotate"
                
                for attr in attrs:
                    cutKey( sel[0], cl=True, t=":", hi="none", at=attr )
                    
                self.getTransformBone();
            
    def delConstraints(self):
        
        if self.getTransformBone():
            sel = ls( sl=True )

            children = listRelatives( sel[0], c=1, ad=1 )
            for child in children:
                if child.type() == 'parentConstraint' \
                        or child.type() == 'scaleConstraint':
                    delete(child)
                    
    def setOffsetAndScale(self):
        
        self.getTransformBone()
        sel = ls(sl=True)
        
        cutKey( sel[0], cl=True, t=":", hi="none", at="translate" )
        cutKey( sel[0], cl=True, t=":", hi="none", at="scale" )
        
        offsetValue = map(float, self.getValuesFromLineEdit(self.offset_layout))
        scaleValue = map(float, self.getValuesFromLineEdit(self.scale_layout)) 
        
        move(offsetValue[0], offsetValue[1], offsetValue[2], sel, a=True)
        scale(sel, scaleValue)
        
        timeline = self.getTimelineMinMax()
        
        for frame in range(int(timeline[0]), int(timeline[1] + 1)):
            
            currentTime(frame)
            
            setKeyframe( sel[0], at="translate")
            setKeyframe( sel[0], at="scale")
        
    def getValuesFromLineEdit(self, layout):
        
        xyzValues = []
        widgets = (layout.itemAt(i).widget() for i in range(layout.count()))
        
        for widget in widgets:
            if isinstance(widget, QtWidgets.QLineEdit):
                xyzValues.append(widget.text())
                
        return xyzValues

    def getFolderPath(self):

        filePath = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder", "")    
        if filePath:
            self.filepath_le.setText(filePath)
    
    def checkForEmptyLineEdit(self, txtField):
        
        if not txtField.text():
            return False
        else:
            return True
        
    def createAnimClip(self, arg_string):
        
        mel.eval( 'FBXExportSplitAnimationIntoTakes -v ' + arg_string )  
        
    def clearCreateAnimClip(self, arg_string):
        
        mel.eval( 'FBXExportSplitAnimationIntoTakes -clear;' )
        mel.eval( 'FBXExportSplitAnimationIntoTakes -v ' + arg_string )
            
    def startExport(self):
        
        mel.eval( "FBXExportSplitAnimationIntoTakes -clear;" )
        
        layout = self.clip_main_layout
        
        rows = (layout.itemAt(i).layout() for i in range(layout.count() -1))
        
        for row in rows:
            
            clipArgs = []
            
            multipleFiles = self.SavMult_radbtn.isChecked()
            
            if isinstance(row, QtWidgets.QHBoxLayout):
                for j in range(row.count()):
                    widget = row.itemAt(j).widget()
                    if isinstance(widget, QtWidgets.QLineEdit):
                        text =  widget.text()
                        if text.isdigit():
                            clipArgs.append(float(widget.text()))
                        else:
                            self.clipName = widget.text()
                            clipArgs.append(self.clipName)
                        
            arg_string = " ".join(map(self.stringify, clipArgs))
            
            if (multipleFiles):
                self.clearCreateAnimClip(arg_string)
                self.exportAnimClipsFBX()
            else:
                self.createAnimClip(arg_string)
        if not (multipleFiles):
            self.exportAnimClipsFBX()
            
    def exportAnimClipsFBX(self):
        
        mel.eval( "FBXExportAnimationOnly -v true;" )
        
        mel.eval( "FBXExportDeleteOriginalTakeOnSplitAnimation -v true;")
        
        self.getTransformBone()
        
        if not self.checkForEmptyLineEdit(self.filepath_le):
            self.getFolderPath()
        if self.SavSngl_radbtn.isChecked():
            if not self.checkForEmptyLineEdit(self.filename_le):
                self.genericWarning("Please choose file name")
                return
        
        filePath = self.filepath_le.text() + "/" + self.getFileName()
        
        mel.eval( 'FBXExport -f "%s" -s' % filePath )
                
    def genericWarning(self, message):
            confirmDialog( title=message, button='Okay', defaultButton='Okay', cancelButton='Okay', dismissString='Okay', icn='warning' )


if __name__ == "__main__":

    try:
        testDialog.close() # pylint: disable=E0601
        testDialog.deleteLater()
    except:
        pass

    testDialog = AnimationExporter()
    testDialog.show()