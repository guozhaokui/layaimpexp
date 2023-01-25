
import bpy, bmesh, mathutils
from bpy.props import *
import os
import LMFile

class BlenderImporter(object):
    """doc"""

    def importLm(self, filename):
        lm = LMFile()
        lm.parse(filename)

        meshName = os.path.basename(filename)
        mesh = bpy.data.meshes.new(meshName)
        obj  = bpy.data.objects.new(meshName, mesh)


    def importLH(self, filename):
        """"""