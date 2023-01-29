
import json
import os

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

class Component:
    def __init__(self):
        pass

class Mesh:
    def __init__(self):
        self.src=''

class MeshFilter(Component):
    def __init__(self):
        self.sharedMesh=Mesh()
        pass


class MeshRenderer(Component):
    def __init__(self):
        self.castShadow=True
        self.receiveShadow=True
        self.localBounds=None
        
    pass

class SkinnedMeshRenderer(MeshRenderer):
    def __init__(self):
        self._bones=[]
        self.rootBone=None
        pass


class Material:
    def __init__(self):
        pass

class Sprite3D:
    def __init__(self):
        self._id='0'
        self.name="Object"
        self.transform=Transform()
        self.components:list[Component]=[]
        self.child:list[Sprite3D]=[]


class RefObj:
    AllRefObj=[]
    def __init__(self,obj,key,refid:str):
        self.obj=obj
        self.key=key
        self.refid=refid
        RefObj.AllRefObj.append(self)


class LHFile:
    """
    加载lh文件,解析成对象,
    加载所有相关的lmat文件
    加载所有相关的贴图文件
    具体的blender对象在BlenderImporter中实现
    """
    def parse(self,file:str):
        f = open(file,'r')
        data = f.read()
        fobj = json.loads(data)
        ret:Sprite3D=None
        if "_$ver" in fobj:
            ret = self.parse3(fobj)
        else:
            ret = self.parse2(fobj)
        return ret

    def parse3(self,obj, curobj=None):
        ret = self._parse3(obj,curobj)
        #解决 _$ref 
        self.parse3link(ret)
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

    def parse3link(self,obj):
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
                # if i=='sharedMaterials':
                #     pass
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
                        cc.src=obj[i]
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
        pass


##test
if __name__ == "__main__":
    ff = LHFile()
    #ff.parse('D:/work/layaimpexp/test/muzhalan.lm')
    ff.parse('D:/work/air3_layame/LayaMetaX/dist/res/face/head/head.lh')    #3.0
    #ff.parse('D:/work/air3_layame/LayaMetaX/dist/res/layaverse/weiqiang/weiqiang7.lh')  #2.0
    pass    