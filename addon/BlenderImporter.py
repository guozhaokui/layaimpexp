
import bpy, bmesh, mathutils
from bpy.props import *
import os
import LMFile

class BlenderImporter(object):
    """doc"""

    def importLm(self, filename):
        lm = LMFile.LMFile()
        meshinfo = lm.parse(filename)

        meshName = os.path.basename(filename)
        mesh = bpy.data.meshes.new(meshName)
        obj  = bpy.data.objects.new(meshName, mesh)

        if hasattr(bpy.context.scene, "cursor_location"):
            obj.location = bpy.context.scene.cursor_location
            bpy.context.scene.objects.link(obj)
        elif hasattr(bpy.context.scene.cursor, "location"):
            obj.location = bpy.context.scene.cursor.location
            bpy.context.collection.objects.link(obj)

        #mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[],[(0,1,2,3)])
        mesh.from_pydata(meshinfo.vb, [], meshinfo.ib)

    def importLH(self, filename):
        """"""

