
import bpy, bmesh, mathutils
from bpy.props import *
import os
import LMFile
import LHFile

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
        # 参数是顶点，边，面。 面可以是3或者4个
        mesh.from_pydata(meshinfo.vb, [], meshinfo.ib)
        mesh.update()

        # 要加uv需要bmesh
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            bm.verts.ensure_lookup_table()
            if(len(meshinfo.uv0)>0):
                self.createTextCoord(bm,0,meshinfo.uv0)
            bm.to_mesh(mesh)
        finally:
            bm.free()

    def createTextCoord(self,bm:bmesh,uvlayer:int,uvdata:list):
        uv_lay = bm.loops.layers.uv.new('uv_' + str(uvlayer))
        for face in bm.faces:
            for vv in face.loops:
                uv = vv[uv_lay].uv
                vertIndex = vv.vert.index
                datauv = uvdata[vertIndex]
                uv.x=datauv[0]
                #不知道为什么要反转，否则效果不对
                uv.y=1-datauv[1]


    def addMtl(matName:str):
        #new创建的自带一个 Principled BSDF 节点，所以下面选择就行了
        mat = bpy.data.materials.new(matName)
        mat.use_nodes = True    #blender的use node
        baseColorConnected = False
        bsdf = mat.node_tree.nodes["Principled BSDF"]  #   Diffuse BSDF?
        # 创建一个新的贴图节点，具体类型可以添加后看看script的type
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        img = bpy.data.images.load(fullpath)
        texImage.image = img
        mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
        pass

    def importLH(self, filename):
        lh = LHFile.LHFile()
        lh.parse(filename)
        """"""

