import maya.standalone
maya.standalone.initialize()
import os
import maya.cmds as cmds

path = 'D:\TestDir'
prefix = 'male'
suffix = ".ma"

exclude = 'torso.00'

renameMod = "_colorCorrect"

males = []
for dirpath, subdirs, files in os.walk(path):
    males.extend(os.path.join(dirpath, mayafile) for mayafile in files if mayafile.startswith(prefix) and mayafile.endswith(suffix))

for filepath in males:
    
    if not exclude in filepath:

        cmds.file( filepath, o=True )

        #Turn on color management
        cmds.colorManagementPrefs(e=True, cme=True)

        #set all normal textures to raw colorspace
        files = cmds.ls(type='file')
        normalTag = "norm"
        for file in files:
                texFileName = cmds.getAttr("%s.fileTextureName" % file)
                fileSplit = texFileName.split(".")
                fileName = fileSplit[0]
                fileTypeSplit = fileName.split("_")
                fileType = fileTypeSplit[-1]
                
                if fileType == normalTag:           
                    cmds.setAttr(file + '.colorSpace', 'Raw', type='string')

        #save file over itself

        newFileName = filepath.rsplit(".",1)[0] + renameMod + suffix
        
        cmds.file(rename = newFileName)
            
        cmds.file(f=True, type='mayaAscii', save=True )
    
maya.standalone.uninitialize()