import maya.cmds as cmds
from pymel.core.general import Attribute



def transferAnim():
    
    sel = cmds.ls("*Puppet_*", type='joint')
    dynamic_sel = cmds.ls(sl=True)

    dyn_bones = []
    
    for each in dynamic_sel:
        dyn_bones.append(each.split(':')[1])

    minAnimTime = cmds.playbackOptions(q=True, min=True)
    maxAnimTime = cmds.playbackOptions(q=True, max=True)


    for frame in range(int(minAnimTime), int(maxAnimTime + 1)):
        
        cmds.currentTime(frame)
        
        for bone in sel:
            
            for dyn_bone in dyn_bones:
                
                if bone == dyn_bone:
                    
                    dyn_index = dyn_bones.index(dyn_bone)
                    
                    x = dynamic_sel[dyn_index]
                    
                    cmds.matchTransform(x, bone, piv=0, pos=0, rot=1, scl=1)
                    cmds.setKeyframe(x)
                    
def resetBones():
    
    orig_rig = cmds.ls("*Temp_Rig:*Puppet*", type='joint')
    new_rig = cmds.ls("*Dynamic_Rig:*Puppet*", type='joint')

    for each in range(len(orig_rig)):
        
        old = orig_rig[each]
        new = new_rig[each]
        
        cmds.select( old, r=True )
        
        for new_bone in new_rig:
            
            if old.split(":")[1] == new_bone.split(":")[1]:
                old_rot = cmds.xform( q=True, ro=True, r=True )
                old_pos = cmds.xform( q=True, t=True, r=True )
                old_scl = cmds.xform( q=True, s=True, r=True )
                
                print(old)
                print(new_bone)
                
                cmds.cutKey(new_bone, cl=True)
                
                new_bone = str(new_bone)
                
                cmds.setAttr( new_bone + ".rotate", old_rot[0], old_rot[1], old_rot[2] )
                cmds.setAttr( new_bone + ".translate", old_pos[0], old_pos[1], old_pos[2] )
                cmds.setAttr( new_bone + ".scale", old_scl[0], old_scl[1], old_scl[2] )
                
                
def headAdjustment():
    
    minAnimTime = cmds.playbackOptions(q=True, min=True)
    maxAnimTime = cmds.playbackOptions(q=True, max=True)


    for frame in range(int(minAnimTime), int(maxAnimTime + 1)):
        
        cmds.currentTime(frame)
    
        orig_vert = cmds.ls("Puppet_Geo.vtx[1427]")
        new_vert = cmds.ls("Dynamic_Rig:Bonbon_Geo.vtx[1427]")
        
        orig_pt = cmds.pointPosition(orig_vert[0], w=True)
        new_pt = cmds.pointPosition(new_vert[0], w=True)
        
        diffx = orig_pt[0] - new_pt[0]
        diffy = orig_pt[1] - new_pt[1]
        diffz = orig_pt[2] - new_pt[2]
        
        print(diffx, diffy, diffz)
        
        cmds.move( diffx, diffy, diffz, "Dynamic_Rig:Puppet_Head_Bn", relative=True )
        
        cmds.setKeyframe( "Dynamic_Rig:Puppet_Head_Bn", at='translate')
        
def createnamespaces():
    
    cmds.namespace( add='Dynamic_Rig' )
    cmds.namespace( add='Temp_Rig' )
    
    
createnamespaces()
   
resetBones()

transferAnim()

headAdjustment()