
import json
import os

from numpy import NaN

import LMFile
from LMFile import Mesh
from Loader import load,LoadType,normalize_path
import struct

class Vector3:
    def __init__(self,x=0,y=0,z=0):
        self.x=x
        self.y=y
        self.z=z
    def set(self,x,y,z):
        self.x=x
        self.y=y
        self.z=z
    def copy(self,b):
        self.set(b.x,b.y,b.z)
    def length(self):
        return (self.x**2+self.y**2+self.z**2)**0.5

class Vector4:
    def __init__(self,x=0,y=0,z=0,w=0):
        self.x=x
        self.y=y
        self.z=z
        self.w=w

    def set(self,x,y,z,w):
        self.x=x
        self.y=y
        self.z=z
        self.w=w

    def copy(self,b):
        self.set(b.x,b.y,b.z,b.w)
    def length(self):
        return (self.x**2+self.y**2+self.z**2, self.w**2)**0.5

class Quaternion:
    def __init__(self,x=0,y=0,z=0,w=1):
        self.x=x
        self.y=y
        self.z=z
        self.w=w
    def set(self,x,y,z,w):
        self.x=x
        self.y=y
        self.z=z
        self.w=w
    def copy(self,b):
        self.set(b.x,b.y,b.z,b.w)
        
class Matrix4x4:
    pass

class Bounds:
    def __init__(self):
        self.min=Vector3()
        self.max=Vector3()

class Transform:
    def __init__(self):
        self._localPosition=Vector3()
        self._localScale=Vector3(1.0,1.0,1.0)
        self._localRotation=Quaternion()

    @property
    def localRotation(self):
        return self._localRotation
    @localRotation.setter
    def localRotation(self,r:Quaternion):
        self._localRotation.copy(r)

    @property
    def localPosition(self):
        return self._localPosition
    @localPosition.setter
    def localPosition(self,v:Vector3):
        self._localPosition.copy(v)

    @property
    def localScale(self):
        return self._localScale
    @localScale.setter
    def localScale(self,v:Vector3):
        self._localScale.copy(v)
        


class Component:
    def __init__(self):
        pass

class MeshFilter(Component):
    def __init__(self):
        super().__init__()
        self.sharedMesh=Mesh()
        pass


class MeshRenderer(Component):
    def __init__(self):
        super().__init__()
        self.castShadow=True
        self.receiveShadow=True
        self.localBounds=None
        self.sharedMaterials=[]
        self.materials=[]
        
    pass

class SkinnedMeshRenderer(MeshRenderer):
    def __init__(self):
        super().__init__()
        self._bones=[]
        self.rootBone=None
        pass

class PhyMesh:
    def __init__(self) -> None:
        self._id='0'
        self.name="Object"
        self.transform=Transform()
        self.meshPath=""


class Texture:
    def __init__(self):
        self.linear=False
        self.image=''
        self.blenderobj=None
        pass

class Material:
    def __init__(self):
        self._src=''
        self.diffuseColor=[]
        self.diffuseTexture=None
        self.normalTexture=None
        self.texturelist = []
        self.textures = {}
        self.emissionTexture=None
        self.metallicValue=0
        self.metallicTexture=(None,'r') #贴图，通道. type()==tuple
        self.smoothValue=0
        self.smoothTexture=None
        self.blenderobj=None
        self.shaderPath=None

    @property
    def src(self):
        return self._src

    @src.setter
    def src(self,url:str):
        self._src=url
        self.parseMtl(url)

    def parseMtl(self,url:str):
        # f = open(url,'r')
        # data = f.read()
        data = load(url,LoadType.TEXT)
        fobj = json.loads(data)
        if "version" in fobj:
            ver = fobj['version']
            if ver=='LAYAMATERIAL:04':
                self.parse04(fobj,url)
            elif ver=='LAYAMATERIAL:02':
                self.parse02(fobj,url)
            elif ver=='LAYAMATERIAL:03':
                self.parse03(fobj,url)
        pass

    def parse02(self,obj,url:str):
        self.parse03(obj,url)
        pass
    def parse03(self,obj,url:str):
        props = obj['props']
        type = props['type']
        textures = props['textures']
        mtlpath = os.path.dirname(url)
        if type=='Laya.LayaMePBRMergeMaterial':
            for t in textures:
                name=t['name']
                absfile= None
                if 'path' in t:
                    path = t['path']
                    absfile = normalize_path(os.path.join(mtlpath,path))
                texture = assetsMgr.getAsset(absfile)
                #texture.linear=t['constructParams'][5]
                if name=='u_MergeTexture':
                    self.diffuseTexture = texture
                if name=='u_MergeTexture1':
                    self.metallicTexture=(texture,'a')
                    self.smoothTexture =(texture,'r')
                    pass
            pass
        elif type =='Laya.BlinnPhongMaterial':
            if 'enableVertexColor' in props:
                pass
            for t in textures:
                name=t['name']
                absfile= None
                if 'path' in t:
                    path = t['path']
                    absfile = normalize_path(os.path.join(mtlpath,path))
                texture = assetsMgr.getAsset(absfile)
                #texture.linear=t['constructParams'][5]
                if name=='albedoTexture':
                    self.diffuseTexture = texture
            for v in props['vectors']:
                name = v['name']
                if name=='specularColor':
                    pass
                elif name=='albedoColor':
                    pass
                pass
            pass
        else:
            pass
        pass
    def parse04(self,obj,url:str):
        props = obj['props']
        type = props['type']
        textures = props['textures'] if 'textures' in props else []
        mtlpath = os.path.dirname(url)

        for t in textures:
            name=t['name']
            absfile= None
            if 'path' in t:
                path = t['path']
                absfile = normalize_path(os.path.join(mtlpath,path))
                texture = assetsMgr.getAsset(absfile)
                self.texturelist.append(texture)
                self.textures[name] = texture

            #texture.linear=t['constructParams'][5]

        if type=='PBR':
            if 'u_AlbedoTexture' in self.textures:
                self.diffuseTexture = self.textures['u_AlbedoTexture']
                # u_NormalTexture  u_OcclusionTexture u_EmissionTexture u_MetallicGlossTexture
        elif type =='MergePBR':
            if 'u_AlbedoTexture' in self.textures:
                self.diffuseTexture = self.textures['u_AlbedoTexture']
                self.diffuseColor = props['u_AlbedoColor'] if 'u_AlbedoColor' in props else None
                self.smoothValue = props['u_Smoothness'] if 'u_Smoothness' in props else NaN
                self.metallicValue = props['u_Metallic'] if 'u_Metallic' in props else NaN
                self.shaderPath = props['shaderPath'] if 'shaderPath' in props else None
            pass
        elif type =='GlassMaterial':
            if 'u_TextureCube' in self.textures:
                pass
            if 'u_Refraction' in self.textures:
                pass
            pass
                

class Material04:
    pass

class Sprite3D:
    def __init__(self):
        self._id='0'
        self.name="Object"
        self.transform=Transform()
        self.components:list[Component]=[]
        self.child:list[Sprite3D]=[]
        self.parent=None
        self.parent_bone=None
        self.isBone=False
        #如果是骨骼的话 ，需要记录一个根，这样任意挂在该骨骼上的物体都容易找到parent
        self.boneRefArmature = None
        self.blender_bone = None
        # 材质数组，用来分给submesh
        self.mtls = []

    def getMesh(self):
        for index,c in enumerate(self.components):
            if isinstance(c,MeshFilter):
                return index
        return -1

    def getArmature(self):
        for index,c in enumerate(self.components):
            if isinstance(c,SkinnedMeshRenderer):
                return index
        return -1

class LHScene(Sprite3D):
    def __init__(self):
        super().__init__()
        self.root=None
        self.objects:list[Sprite3D]=[]
        self.armatures=None
        self.assets=None

class RefObj:
    AllRefObj=[]
    def __init__(self,obj,key,refid:str):
        self.obj=obj
        self.key=key
        self.refid=refid
        RefObj.AllRefObj.append(self)

class Assets:
    def __init__(self):
        self.mtls={}
        self.imgs={}
        self.meshes={}

    def getAsset(self,url:str):
        url = normalize_path(url)
        ext:str = (os.path.splitext(url)[-1]).lower()
        if ext=='.lh':
            pass
        elif ext=='.lmat':
            if url in self.mtls:
                return self.mtls[url]
            mtl = Material()
            mtl.parseMtl(url)
            self.mtls[url]=mtl
            return mtl
        elif ext=='.lm':
            if url in self.meshes:
                return self.meshes[url]
            mesh = LMFile.LMFile()
            meshinfo = mesh.parse(url)
            self.meshes[url]=meshinfo
            return meshinfo
        elif ext=='.png' or ext=='.jpg':
            if url in self.imgs:
                return self.imgs[url]
            texture = Texture()
            texture.image=url
            self.imgs[url]=texture
            return texture
        else:
            pass
        

assetsMgr = Assets()

class LHFile:
    """
    加载lh文件,解析成对象,
    加载所有相关的lmat文件
    加载所有相关的贴图文件
    具体的blender对象在BlenderImporter中实现
    """
    def __init__(self) -> None:
        self.lhfile=''
        # lh所在目录
        self.lhpath=''
        
    def parse(self,file:str):
        self.lhfile=file
        self.lhpath = os.path.dirname(file)
        data = load(file,LoadType.TEXT)
        fobj = json.loads(data)
        root:Sprite3D=None
        if "_$ver" in fobj:
            root = self.parse3(fobj)
        else:
            root = self.parse2(fobj)

        ret = LHScene()
        ret.root=root
        ret.armatures=self.gatherArmature(root,{})
        ret.objects = self.gatherObjects(root,[])
        ret.assets = assetsMgr
        return ret

    def gatherObjects(self,root:Sprite3D,objects:list[Sprite3D]):
        def _gatherObjects(obj:Sprite3D):
            if not obj.isBone:
                objects.append(obj)
                for oc in obj.child:
                    _gatherObjects(oc)
        _gatherObjects(root)
        return objects

    def gatherArmature(self,root:Sprite3D,armatures):
        def _gatherArmature(obj:Sprite3D):
            for c in obj.components:
                if isinstance(c,SkinnedMeshRenderer):
                    rootsp:Sprite3D = c.rootBone
                    armatures[rootsp._id] = rootsp
                    for b in c._bones:
                        b.isBone=True
                        b.boneRefArmature=rootsp
            for child in obj.child:
                _gatherArmature(child)
            pass
        _gatherArmature(root)
        return armatures


    def parse3(self,obj, curobj=None):
        ret = self._parse3(obj,curobj)
        #解决 _$ref 
        self.parselink(ret)
        return ret

    def _findByID(self, id:str,obj:Sprite3D):
        if obj._id == id:
            return obj
        if len(obj.child)==0:
            return None
        for c in obj.child:
            r = self._findByID(id,c)
            if r:
                return r
        return None

    def parselink(self,obj):
        all = RefObj.AllRefObj
        for r in all:
            find = self._findByID(r.refid,obj)
            if find:
                if type(r.key)==int:
                    r.obj[r.key]=find
                else:
                    setattr(r.obj,r.key,find)

        RefObj.AllRefObj=[]
        pass

    def _parse3(self,obj, curobj=None):
        if '_$type' not in obj and not curobj:
            return None
        cc:Sprite3D=curobj
        typecls=None
        if not cc:
            _type = obj['_$type']
            allcls = globals()
            typecls = allcls[_type]
            cc = typecls()
        if( hasattr(cc,"parse3")):
            cc.parse3(obj)
        else:
            keys = list(obj.keys())
            for i in keys:
                if i=='sharedMaterials':
                    pass
                    a=1
                    pass
                if str.startswith(i,'_$'):
                    if i=='_$child':
                        children:list[object] = obj['_$child']
                        for c in children:
                            childobj = self._parse3(c)
                            if childobj:
                                cc.child.append(childobj)
                        pass
                    elif i=='_$comp':
                        comps = obj['_$comp']
                        for c in comps:
                            comp = self._parse3(c)
                            if comp:
                                cc.components.append(comp)
                            pass
                        pass
                    elif i=='_$id':
                        cc._id=obj[i]
                        pass
                    elif i=='_$uuid':
                        src = obj[i]
                        abssrc = normalize_path(os.path.join(self.lhpath,src))
                        asset = assetsMgr.getAsset(abssrc)
                        if typecls and not isinstance(asset,typecls):
                            print('error')
                        else:
                            cc = asset
                        
                        if isinstance(asset, Material):
                            #添加到材质列表中
                            cc.mtls.append(asset)
                            pass
                        #cc.src=abssrc

                        pass
                    elif i=='_$ref':
                        pass
                else:
                    #如果是个对象，则要解析对象
                    valuetype = type(obj[i])
                    if valuetype == dict:
                        #判断是不是ref对象
                        if "_$ref" in obj[i]:
                            setobj = RefObj(cc,i,obj[i]['_$ref'])
                        setobj = None
                        if '_$type' in obj[i]:
                            setobj = self._parse3(obj[i])
                        else:
                            setobj = self._parse3(obj[i],getattr(cc,i))
                        setattr(cc,i,setobj)
                    elif valuetype==list:
                        #例如 sharedMaterials， _bones
                        # 数组要每次单独处理
                        setv=[]
                        for index,v in enumerate(obj[i]):
                            #判断是不是ref对象
                            if "_$ref" in v:
                                setv.append(RefObj(setv,index,v['_$ref']))
                            elif "_$uuid" in v:
                                src = v["_$uuid"]
                                abssrc = normalize_path(os.path.join(self.lhpath,src))
                                asset = assetsMgr.getAsset(abssrc)
                                if typecls and not isinstance(asset,typecls):
                                    print('error')
                                else:
                                    cc = asset
                                setv.append(asset)
                                # if isinstance(asset, Material):
                                #     #添加到材质列表中
                                #     cc.mtls.append(asset)
                                #     pass

                                pass
                            else:
                                setobj = None
                                if '_$type' in v:
                                    setobj = self._parse3(v)
                                else:
                                    pass
                                setv.append(setobj)
                        setattr(cc,i,setv)
                        pass
                    else:
                        setattr(cc,i,obj[i])
                pass
            pass
        return cc
        # _$type Sprite3D
        # name 
        # transform
        #   localRotation
        # _$child
        # _$comp

    def parse2(self,obj):
        if 'version' not in obj:
            return None
        if 'data' not in obj:
            return None
        version = obj['version']
        if version == 'LAYAHIERARCHY:02':
            rootobj= Sprite3D()
            self.parse2data(obj['data'],rootobj)
            self.parselink(rootobj)
            return rootobj
        else:
            print ('不支持的版本',version)
            return None
        pass

    def parse2data(self,obj,parent):
        if not 'type' in obj:
            return None
        type = obj['type']
        meshfilter:MeshFilter=None
        meshRender:MeshRenderer=None
        if type == 'MeshSprite3D':
            cc = Sprite3D()
            meshfilter = MeshFilter()
            meshRender = comp2 = MeshRenderer()
            cc.components.append(meshfilter)
            cc.components.append(comp2)
            pass
        elif type == 'SkinnedMeshSprite3D':
            cc = Sprite3D()
            meshfilter = MeshFilter()
            meshRender = comp = SkinnedMeshRenderer()
            cc.components.append(meshfilter)
            cc.components.append(comp)
            pass
        else:
            allcls = globals()
            typecls = allcls[type]
            cc:Sprite3D = typecls() 
        if 'instanceID' in obj:
            cc._id=obj['instanceID']
            
        if 'props' in obj:
            props = obj['props']
            trans = Transform()
            for p in props:
                if p=='position':
                    posarr = props['position']
                    vpos = Vector3(posarr[0],posarr[1],posarr[2])
                    trans.localPosition=vpos
                elif p=='rotation':
                    qarr = props['rotation']
                    quat = Quaternion(qarr[0],qarr[1],qarr[2],qarr[3])
                    trans.localRotation=quat
                elif p=='scale':
                    sarr = props['scale']
                    scale = Vector3(sarr[0],sarr[1], sarr[2])
                    trans.localScale=scale
                elif p == 'meshPath':
                    if meshfilter:
                        absfile = normalize_path(os.path.join(self.lhpath,props[p]))
                        meshfilter.sharedMesh = assetsMgr.getAsset(absfile)
                elif p == 'materials':
                    mtls = props[p]
                    for m in mtls:
                        if 'path' in m:
                            absfile = normalize_path(os.path.join(self.lhpath,m['path']))
                            mtlobj = assetsMgr.getAsset(absfile)
                            #if meshRender:
                            #    meshRender.materials.append(mtlobj)
                            cc.mtls.append(mtlobj)

                elif p == 'rootBone':
                    skinnrender:SkinnedMeshRenderer = meshRender
                    if skinnrender:
                        setv = RefObj(skinnrender,'rootBone',props[p])
                        skinnrender.rootBone=setv
                        pass
                    pass
                elif p == 'bones':
                    skinnrender:SkinnedMeshRenderer = meshRender
                    if skinnrender:
                        bones = props[p]
                        for index,b in enumerate(bones):
                            setv = RefObj(skinnrender._bones, index, b)
                            skinnrender._bones.append(setv)
                else:
                    setattr(cc,p,props[p])
                pass
            cc.transform=trans
            
        if 'components' in obj:
            comps = obj['components']
            for c in comps:
                pass
            pass
        if 'child' in obj:
            child = obj['child']
            for c in child:
                self.parse2data(c,cc)
                pass
            pass
        if parent:
            cc.parent=parent
            parent.child.append(cc)
        return cc


class LayaMePBRMaterial:
    def __init__(self) -> None:
        self.name=''
        self.diffuse=[1,1,1]
        self.smooth=0
        self.metallic=0
        self.emission=[0,0,0]

class LHMatsFile:
    def __init__(self) -> None:
        self.f=None
        #self.meshpath=''
        self.mesh:Mesh=None
        self.mtlnames=[]
        self.mtls:list[LayaMePBRMaterial]=[]
        
    def parse(self, file:str):
        self.mtls=[]
        self.mtlnames=[]
        self.lhfile=file
        self.lhpath = os.path.dirname(file)
        self.f = load(file,LoadType.IO)
        len = self.readU16()
        tag = self.readString(len)
        if(tag=='LAYALHMATS:01'):
            pass
        elif (tag=='LAYALHMATS:0101'):
            self.parse02()
            pass
        elif (tag=='LAYALHMATS:02'):
            pass
        root:Sprite3D=None
        pass

    def parse02(self):
        strLen = self.readU16()
        meshpath = self.readString(strLen)
        if len(meshpath)>1 :
            absfile = normalize_path(os.path.join(self.lhpath,meshpath))
            self.mesh  = assetsMgr.getAsset(absfile)

        cnt = self.readU16()
        for i in range(cnt):
            strLen = self.readU16()
            self.mtlnames.append(self.readString(strLen))

        arraylen = self.readU32()
        for i in range(cnt):
            cmtl = LayaMePBRMaterial()
            cmtl.diffuse = [self.readU8(),self.readU8(),self.readU8()]
            cmtl.metallic = self.readU8()
            cmtl.smooth = self.readU8()
            cmtl.emission = [self.readU8(),self.readU8(),self.readU8()]
            self.mtls.append(cmtl)

    def readString(self,len):
        str = b''
        for i in range(len):
            c = self.f.read(1)
            if not c:
                return None

            if c == b'\0' or c == b'':
                return str.decode()
            else:
                str = str + c

        return str.decode()

    def readU16(self):
        v = self.f.read(2)
        if not v:
            return None
        return struct.unpack('H', v)[0]

    def readU8(self):
        v = self.f.read(1)
        if not v:
            return None
        return struct.unpack('B', v)[0]

    def readU32(self):
        v = self.f.read(4)
        if not v:
            return None
        return struct.unpack('I', v)[0]



##test
if __name__ == "__main__":
    ff = LHFile()
    #ff.parse('D:/work/layaimpexp/test/muzhalan.lm')
    #ff.parse('D:/work/layaimpexp/test/skinnerTest/femalezhenghe.lh')
    #ff.parse('D:/work/laya/air3_layame/LayaMetaX/dist/res/model/42_baoting.lh')
    #ff.parse('D:/work/laya/air3_layame/LayaMetaX/dist/res/face/head/head.lh')    #3.0
    #ff.parse('D:/work/air3_layame/LayaMetaX/dist/res/layaverse/weiqiang/weiqiang7.lh')  #2.0

    ff1 = LHMatsFile()
    ff1.parse('https://oss.layabox1-beijing.layabox.com/upload/svn/resource/model/plant/shu03.lhmats')
    pass    