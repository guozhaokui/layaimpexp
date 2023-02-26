
from numpy import number
import bpy, bmesh
from mathutils import Vector, Quaternion, Matrix
from bpy.props import *
from bpy_extras.image_utils import load_image
import os
import LMFile
import LHFile
from Loader import load,LoadType,normalize_path

class VNode:
    # Types
    Object = 0
    Bone = 1
    DummyRoot = 2

    def __init__(self) -> None:
        self.base_trs = (
            Vector((0, 0, 0)),
            Quaternion((1, 0, 0, 0)),
            Vector((1, 1, 1)),
        )
        self.name = None
        self.default_name = 'Node'  # fallback when no name
        self.children = []
        self.parent = None
        self.type = VNode.Object
        self.is_arma = False
        self.base_trs = (
            Vector((0, 0, 0)),
            Quaternion((1, 0, 0, 0)),
            Vector((1, 1, 1)),
        )
        # Additional rotations before/after the base TRS.
        # Allows per-vnode axis adjustment. See local_rotation.
        self.rotation_after = Quaternion((1, 0, 0, 0))
        self.rotation_before = Quaternion((1, 0, 0, 0))


    def trs(self):
        # (final TRS) = (rotation after) (base TRS) (rotation before)
        t, r, s = self.base_trs
        m = scale_rot_swap_matrix(self.rotation_before)
        return (
            self.rotation_after @ t,
            self.rotation_after @ r @ self.rotation_before,
            m @ s,
        )


def scale_rot_swap_matrix(rot):
    """Returns a matrix m st. Scale[s] Rot[rot] = Rot[rot] Scale[m s].
    If rot.to_matrix() is a signed permutation matrix, works for any s.
    Otherwise works only if s is a uniform scaling.
    """
    m = nearby_signed_perm_matrix(rot)  # snap to signed perm matrix
    m.transpose()  # invert permutation
    for i in range(3):
        for j in range(3):
            m[i][j] = abs(m[i][j])  # discard sign
    return m

def nearby_signed_perm_matrix(rot):
    """Returns a signed permutation matrix close to rot.to_matrix().
    (A signed permutation matrix is like a permutation matrix, except
    the non-zero entries can be ±1.)
    """
    m = rot.to_matrix()
    x, y, z = m[0], m[1], m[2]

    # Set the largest entry in the first row to ±1
    a, b, c = abs(x[0]), abs(x[1]), abs(x[2])
    i = 0 if a >= b and a >= c else 1 if b >= c else 2
    x[i] = 1 if x[i] > 0 else -1
    x[(i+1) % 3] = 0
    x[(i+2) % 3] = 0

    # Same for second row: only two columns to consider now.
    a, b = abs(y[(i+1) % 3]), abs(y[(i+2) % 3])
    j = (i+1) % 3 if a >= b else (i+2) % 3
    y[j] = 1 if y[j] > 0 else -1
    y[(j+1) % 3] = 0
    y[(j+2) % 3] = 0

    # Same for third row: only one column left
    k = (0 + 1 + 2) - i - j
    z[k] = 1 if z[k] > 0 else -1
    z[(k+1) % 3] = 0
    z[(k+2) % 3] = 0

    return m

def isImageLoaded(img):
    if (0==img.size[0]) and (img.size[1]==0):
        return False
    return True


class ExportSetting:
    def __init__(self) -> None:
        self.onlySelected=True
        self.useMeshVertexDecl=True

class BlenderImporter(object):
    """doc"""

    def importLm(self, filename):
        lm = LMFile.LMFile()
        meshinfo = lm.parse(filename)

        meshName = os.path.basename(filename)
        mesh = self.creatMesh(meshName,meshinfo)
        obj  = bpy.data.objects.new(meshName, mesh)

        if hasattr(bpy.context.scene, "cursor_location"):
            obj.location = bpy.context.scene.cursor_location
            bpy.context.scene.objects.link(obj)
        elif hasattr(bpy.context.scene.cursor, "location"):
            obj.location = bpy.context.scene.cursor.location
            bpy.context.collection.objects.link(obj)

    def creatMesh(self,meshName:str, meshinfo:LMFile.Mesh):
        mesh = bpy.data.meshes.new(meshName)
        #mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[],[(0,1,2,3)])
        # 参数是顶点，边，面。 面可以是3或者4个
        mesh.from_pydata(meshinfo.vb, [], meshinfo.ib)

        if len(meshinfo.normal)==len(meshinfo.vb):
            self.assignNormals(mesh,meshinfo.normal)    

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

        return mesh


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

    def assignNormals(self,mesh, normals:list[number]):
        mesh.use_auto_smooth = True #必须要设置这个
        #mesh.show_normal_vertex = True
        #mesh.show_normal_loop = True
        # normals的个数必须与顶点数相同
        mesh.normals_split_custom_set_from_vertices(normals)
        pass

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

    def addBone(name:str):
        armature = bpy.data.armatures.new(name)
        obj = bpy.data.objects.new(name, armature)
        #obj.empty_display_size=1.0
        context = bpy.context
        scene = context.scene
        scenename = scene.name
        scene.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        # 转成edit模式
        bpy.ops.object.editmode_toggle()

        #bpy.data.scenes[gltf.blender_scene].collection.objects.link(obj)
        # trans, rot, scale = vnode.trs()
        # obj.location = trans
        # obj.rotation_mode = 'QUATERNION'
        # obj.rotation_quaternion = rot
        # obj.scale = scale

    def createArmature(self,root:LHFile.Sprite3D):
        if not root.isBone:
            return
        name = root.name
        armature = bpy.data.armatures.new(name)
        armature.show_names=True
        armature.display_type = "STICK"        
        obj = bpy.data.objects.new(name, armature)
        #obj.empty_display_size=1.0
        context = bpy.context
        scene = context.scene
        scenename = scene.name
        scene.collection.objects.link(obj)  #TODO 外面做
        context.view_layer.objects.active = obj
        # 转成edit模式
        bpy.ops.object.editmode_toggle()

        #用来计算armature空间的quat
        quat_armature_space = Quaternion((1,0,0,0))
        pos_armature_space = Vector((0,0,0))      #父骨骼的head的位置
        
        def _createbone(sp:LHFile.Sprite3D, parent_head, parent_quat):
            if not sp.isBone:
                #TODO 设置parentbone
                return None
            
            bone = armature.edit_bones.new(sp.name)
            bone.head = [0,0,0]
            sp.blender_bone=bone
            childnum = len(sp.child)

            if childnum>1:
                #多个子，则认为tail是固定长度，固定朝向
                bone.tail = [0,0,0.1]
            elif childnum==1:
                bonelen = sp.child[0].transform.localPosition.length()
                #bone.tail = [0,0,bonelen]
                bone.tail = [0,0,bonelen]
                #bone.use_connect = True
            else:
                return bone

            quat = sp.transform.localRotation

            #上面设置tail了，现在可以变换以便计算世界空间的tail
            # 先本地位置偏移
            localpos = sp.transform.localPosition
            vpos = Vector((localpos.x, localpos.y, localpos.z))
            bone.translate(vpos)
            # 本地偏移以后旋转一下，得到新的本地偏移？
            bone.transform(parent_quat.to_matrix())
            # 相对parent的原点偏移一下
            bone.translate(Vector(parent_head))
            parent_head = bone.head

            # 父骨骼空间的旋转
            current_bone_quat_parent_space = Quaternion((quat.w,quat.x,quat.y,quat.z))
            transform_quat = parent_quat @ current_bone_quat_parent_space
            parent_quat = transform_quat

            for spc in sp.child:
                cbone = _createbone(spc,parent_head,parent_quat)
                if cbone:
                    if childnum==1:
                        # 子的head连接到bone的tail
                        #cbone.use_connect=True
                        pass
                    cbone.parent = bone

            # 设置朝向
            # 设置到正确位置
            return bone

        _createbone(root,pos_armature_space,quat_armature_space)
        # for c in root.child:
        #     _createbone(c)
        #     pass

        #退出编辑模式
        bpy.ops.object.editmode_toggle()


    def testAddBones():
        context = bpy.context

        bones = {}
        # XYZ coordinates of bone head in armature space, WXYZ rotation in quaternions 
        bones["Bone"] = ((-1.48222, -0.194431, -0.383472), (0.953425, 0.01901, -0.300824, 0.011176))
        # 骨骼的方向是y方向，所以子的y位置决定了骨骼的长度
        bones["Bone.001"] = ((0, 3.3363, 0), (0.35458, -0.269697, 0.157483, -0.881326))
        bones["Bone.002"] = ((0, 4.0228, 0), (0.074972, -0.432144, 0.202091, -0.875666))
        bones["Bone.002_nub"] = ((0, 4.7955, 0), (1, 0, 0, 0))

        armature = bpy.data.armatures.new("Armature")
        rig = bpy.data.objects.new("Armature", armature)
        context.scene.collection.objects.link(rig)

        context.view_layer.objects.active = rig
        bpy.ops.object.editmode_toggle()

        for i, bone in enumerate(bones.items()):
            # create new bone
            current_bone = armature.edit_bones.new(bone[0])
            
            # first bone in chain
            if i == 0:
                # create bone at armature origin and set its length
                current_bone.head = [0, 0, 0]
                length = list(bones.values())[i+1][0][1]    #子的[0][1]即position.y 是骨骼的长度
                current_bone.tail = [0, 0, length]

                # rotate bone
                quat_armature_space = Quaternion(bone[1][1])
                current_bone.transform(quat_armature_space.to_matrix())
                
                # set position
                current_bone.translate(Vector(bone[1][0]))

                # save bone, its tail position (next bone will be moved to it) and quaternion rotation
                parent_bone = current_bone
                parent_bone_tail = current_bone.tail
                parent_bone_quat_armature_space = quat_armature_space
                
            # last bone in chain
            elif i == (len(bones) - 1):
                # create bone at armature origin and set its length
                current_bone.head = [0, 0, 0]
                current_bone.tail = [0, 0, 1]   #在父骨骼空间的位置
                
                # rotate bone
                current_bone_quat_parent_space = Quaternion(bone[1][1])
                # like matrices, quaternions can be multiplied to accumulate rotational values
                transform_quat = parent_bone_quat_armature_space @ current_bone_quat_parent_space
                current_bone.transform(transform_quat.to_matrix())

                # set position
                current_bone.translate(Vector(parent_bone_tail))
                
                # connect
                current_bone.parent = parent_bone
                current_bone.use_connect = True
                
            else:
                # create bone at armature origin and set its length
                current_bone.head = [0, 0, 0]
                length = list(bones.values())[i+1][0][1]
                current_bone.tail = [0, 0, length]
                
                # rotate bone
                current_bone_quat_parent_space = Quaternion(bone[1][1])
                # like matrices, quaternions can be multiplied to accumulate rotational values
                transform_quat = parent_bone_quat_armature_space @ current_bone_quat_parent_space
                current_bone.transform(transform_quat.to_matrix())
                
                # set position
                current_bone.translate(Vector(parent_bone_tail))
                
                # connect
                current_bone.parent = parent_bone
                current_bone.use_connect = True
                
                # save bone, its tail position (next bone will be moved to it) and quaternion rotation
                parent_bone = current_bone
                parent_bone_tail = current_bone.tail
                parent_bone_quat_armature_space = transform_quat

        bpy.ops.object.editmode_toggle()

    def createMaterial(self,name:str, mtlinfo:LHFile.Material):
        mtl = bpy.data.materials.new(name)
        mtl.use_nodes = True
        bsdf = mtl.node_tree.nodes["Principled BSDF"] 

        if(mtlinfo.diffuseTexture and mtlinfo.diffuseTexture.blenderobj):
            # 创建一个贴图节点
            texImage = mtl.node_tree.nodes.new('ShaderNodeTexImage')
            texImage.image = mtlinfo.diffuseTexture.blenderobj
            texImage.location.x=100
            texImage.location.y=100
            # 连接到Base Color口上
            mtl.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
        return mtl

    def _createImg(self, fullpath:str):
        loadedImgs=[]
        failedImgs=[]
        img = None
        try:
            if fullpath.startswith('http'):
                #img = load_image(fullpath, bpy.context)
                imgdata = load(fullpath,LoadType.BIN)
                filename = os.path.basename(fullpath)
                filepath = os.path.join(bpy.app.tempdir, filename)
                with open(filepath, "wb") as f:
                    f.write(imgdata)                
                img = bpy.data.images.load(filepath)                    
                img.name = "MyImage"
                #img.filepath = "//"+filename
                #os.remove(filepath)  删除后面isImageLoaded会报错
            else: 
                img = bpy.data.images.load(fullpath)
            if isImageLoaded(img):
                loadedImgs.append(fullpath)
            else:
                failedImgs.append(fullpath)
                bpy.data.images.remove(img)
                img = None
        except Exception as e:
            img = None
        return img

    def importLH(self, filename):
        lh = LHFile.LHFile()
        lhsce = lh.parse(filename)

        assets:LHFile.Assets = lhsce.assets
        # 处理材质
        # 加载所有的贴图
        for k,v in assets.imgs.items():
            img = self._createImg(k)
            if img:
                v.blenderobj = img
        # 创建材质
        i=0
        for k,v in assets.mtls.items():
            name = 'mtl_%d'%i
            i=i+1
            mtl = self.createMaterial(name,v)
            if mtl:
                v.blenderobj=mtl
            pass

        # 给对象设置材质

        # 创建普通对象
        for obj in lhsce.objects:            
            meshindex = obj.getMesh()
            skinrindex = obj.getArmature()
            mesh=None
            if meshindex>=0:
                mehsfilter:LHFile.MeshFilter = obj.components[meshindex]
                minfo = mehsfilter.sharedMesh
                mesh = self.creatMesh(obj.name+'_mesh', minfo)

            bobj = bpy.data.objects.new(obj.name, mesh)

            if skinrindex>=0:
                skin:LHFile.SkinnedMeshRenderer = obj.components[skinrindex]
                self.createArmature(skin.rootBone)
                for b in skin._bones:
                    # 创建vertex group 参数是名称
                    bobj.vertex_groups.new(name='bone_%s'%b.name)

                    pass

            vpos = obj.transform.localPosition
            bobj.location = Vector((vpos.x, vpos.y, vpos.z))
            # 添加到场景中
            bpy.context.collection.objects.link(bobj)            

            #添加材质
            if mesh and len(obj.mtls)>0:
                #TODO 选择材质

                for mtl in obj.mtls:
                    bobj.data.materials.append(mtl.blenderobj)
        pass
        # 创建armature

        """"""

    def exportLH(self, setting:ExportSetting, filename:str,gatherfile=True):
        if setting.onlySelected:
            mesh_obj = bpy.context.selected_objects[0]
            mesh = mesh_obj.data
            for l in mesh.loops:
                pass

        pass
    def exportLM(self, vertexDecl:list[str],filename:str):
        pass
    def exportLMAT(self, filename:str):
        pass
