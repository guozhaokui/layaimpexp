import os
import struct
import Float16

class ChunkInfo:
    def __init__(self,off=0,size=0) -> None:
        self.off=off
        self.size=size

class VertexDeclaration:
    elementSize = {"POSITION":12,"NORMAL":12,"COLOR":16,"UV":8,"UV1":8,"BLENDWEIGHT":16,"BLENDINDICES":4,"TANGENT":16,"NORMAL_BYTE":4}

    def __init__(self,declStr:str) -> None:
        self.declstr=declStr
        flags = self.elements = str.split(declStr,',')
        stride=0
        self.vertele={}
        for i in flags:
            if(self.elementSize[i]==None):
                raise Exception("不支持的顶点元素")
                pass
            else:
                elesize = self.elementSize[i]
                self.vertele[i]=(stride,elesize)
                stride+=elesize
        self.stride = stride

class SubMesh:
    def __init__(self, start:int, count:int) -> None:
        self.ibStart=start
        self.ibCount=count
        #self.mtl=None

class Mesh:
    def __init__(self) -> None:
        self.isV05=False
        self.isCompress=False
        self.strings:list[str]=[]
        self.version=''
        self.data=ChunkInfo()
        self.blocknum=0
        self.blocks=[]
        self.boneNames:list[str]=[]
        self.vb=[]
        self.ib=[]
        self.uv0=[]
        self.uv1=[]
        self.normal=[]
        self.tangent=[]
        self.binnormal=[]
        self.color=[]
        self.boneidx=[]
        self.boneweight=[]
        self.vertexDecl:VertexDeclaration=None
        self.subMesh=[]
        


class LMFile(object):
    def __init__(self):
        # 双下划线表示是私有类型的成员
        self.__errorStr = ""
        self.__filesize=0
        self.__lmfile=None

    def getFileSize(self):
        return self.__fileSize        

    def getErrorString(self):
        return self.__errorStr

    def seek(self, offs):
        self.__lmfile.seek(offs, 0)

    def readBytes(self, sizeInBytes):
        v = self.__lmfile.read(sizeInBytes)
        if not v:
            return None
        return v

    def readU32(self):
        v = self.__lmfile.read(4)
        if not v:
            return None
        return struct.unpack('I', v)[0]

    def readU16(self):
        v = self.__lmfile.read(2)
        if not v:
            return None
        return struct.unpack('H', v)[0]

    def readU8(self):
        v = self.__lmfile.read(1)
        if not v:
            return None
        return struct.unpack('B', v)[0]

    def readVec3(self):
        v = self.__lmfile.read(12)
        if not v: return None
        return struct.unpack('fff',v)

    def readVec4(self):
        v = self.__lmfile.read(16)
        if not v:return None
        return struct.unpack('ffff',v)

    def readCString(self):
        # b''表示用字符表示的二进制，所有后面要decode
        str = b''
        while True:
            c = self.__lmfile.read(1)
            if not c:
                return None

            if c == b'\0' or c == b'':
                return str.decode()
            else:
                str = str + c

    def readString(self,len):
        str = b''
        for i in range(len):
            c = self.__lmfile.read(1)
            if not c:
                return None

            if c == b'\0' or c == b'':
                return str.decode()
            else:
                str = str + c

        return str.decode()


    def parse(self, fileName:str)->Mesh:
        self.__lmfile = open(fileName,"rb")
        self.__lmfile.seek(0, os.SEEK_END)
        self.__fileSize = self.__lmfile.tell()
        self.__lmfile.seek(0, os.SEEK_SET)
        meshinfo = Mesh()
        # 字符串长度
        flaglen = self.readU16()
        flag = meshinfo.version = self.readString(flaglen)
        isV05=False
        isCompress=False
        if(flag=="LAYAMODEL:05" or flag =="LAYAMODEL:0501"):
            isV05=meshinfo.isV05= True
        elif(flag=="LAYAMODEL:COMPRESSION_05" or flag=="LAYAMODEL:COMPRESSION_0501"):
            isV05=meshinfo.isV05= True
            isCompress = meshinfo.isCompress=True
        #chunkinfo={"DATA":{"off":0,"size":0},"BLOCK":[],"STRINGS":{"off":0,"count":0,"strings":[]}}
        if(isV05 ):
            meshinfo.data.off = self.readU32()
            meshinfo.data.size = self.readU32()
            blocknum = meshinfo.blocknum = self.readU16()
            for i in range(blocknum):
                off = self.readU32()
                sz = self.readU32()
                meshinfo.blocks.append(ChunkInfo(off,sz))
            #读字符串
            stroff=self.readU32()
            strcnt=self.readU16()
            curpos = self.__lmfile.tell()
            stroff = meshinfo.data.off+stroff
            self.seek(stroff)
            strings = meshinfo.strings
            for i in range(strcnt):
                len = self.readU16()
                strings.append(self.readString(len))
            #恢复位置
            self.seek(curpos)
            #读block
            for i in range(blocknum):
                self.seek( meshinfo.blocks[i].off)
                #字符串索引
                idx = self.readU16()
                name = strings[idx]
                readFunc = getattr(self,'READ_'+name)
                if(readFunc):readFunc(meshinfo)
        else:
            print ( "不支持的版本", flag)
        return meshinfo

    def READ_MESH(self,meshinfo:Mesh):
        strings = meshinfo.strings
        name= strings[self.readU16()]
        vbcount = self.readU16()
        dataoff =  meshinfo.data.off
        # TODO 多个vb的还没做
        for i in range(vbcount):
            vbstart = dataoff+self.readU32()
            vertexCnt = self.readU32()
            shortIB=True
            if(vertexCnt>65535):
                shortIB=False

            vertexFlags = self.readIdxString(meshinfo)
            meshinfo.vertexDecl = VertexDeclaration(vertexFlags)
            stride=meshinfo.vertexDecl.stride

            #下面是ib信息
            ibstart = meshinfo.data.off + self.readU32()
            iblen = self.readU32()
            ibCnt=int(iblen/4)
            if(shortIB):
                ibCnt=int(iblen/2)

            #下面是bbx
            if(meshinfo.isV05):
                bbxmin = self.readVec3()
                bbxmax = self.readVec3()

            #下面是骨骼信息
            bonecnt = self.readU16()
            for i in range(bonecnt):
                meshinfo.boneNames.append(meshinfo.strings[self.readU16()])
            #bindpose信息
            bindPoseStart = self.readU32()
            bindPoseLen = self.readU32()


            #读vb信息
            if meshinfo.isV05:
                if meshinfo.isCompress:
                    f16 = Float16.HalfFloatUtils()
                    #保存的是简单压缩后的数据，需要边读边解
                    elements = meshinfo.vertexDecl.elements
                    self.seek(vbstart)
                    for vt in range(vertexCnt):
                        for ele in elements:
                            if(ele=="POSITION"):
                                #pos用的是半精度浮点数
                                v = self.readU16()
                                x = f16.convertToNumber(v)
                                v = self.readU16()
                                y = f16.convertToNumber(v)
                                v = self.readU16()
                                z = f16.convertToNumber(v)
                                meshinfo.vb.append((x,y,z))
                                pass
                            elif(ele=="NORMAL"):
                                #normal是uint8[3]
                                vx = self.readU8()
                                vy = self.readU8()
                                vz = self.readU8()
                                meshinfo.normal.append((vx/127.5-1,vy/127.5-1,vz/127.5-z))
                                pass
                            elif(ele=="COLOR"):
                                #color是uint8[4]
                                r=self.readU8() 
                                g=self.readU8()
                                b=self.readU8()
                                a=self.readU8()
                                meshinfo.color.append((r/255.0,g/255.0,b/255.0,a/255.0))
                                pass
                            elif(ele=="UV"):
                                #uv是float16
                                u = self.readU16()
                                v = self.readU16()
                                meshinfo.uv0.append((f16.convertToNumber(u),f16.convertToNumber(v)))
                                pass
                            elif(ele=="UV1"):
                                u = self.readU16()
                                v = self.readU16()
                                meshinfo.uv1.append((f16.convertToNumber(u),f16.convertToNumber(v)))
                                pass
                            elif(ele=="BLENDWEIGHT"):
                                # uint8[4]
                                w1 = self.readU8()
                                w2 = self.readU8()
                                w3 = self.readU8()
                                w4 = self.readU8()
                                meshinfo.boneweight.append((w1/255.0,w2/255.0,w3/255.0,w4/255.0))
                                pass
                            elif(ele=="BLENDINDICES"):
                                i1 = self.readU8()
                                i2 = self.readU8()
                                i3 = self.readU8()
                                i4 = self.readU8()
                                meshinfo.boneidx.append((i1,i2,i3,i4))
                                pass
                            elif(ele=="TANGENT"):
                                #同normal
                                vx = self.readU8()
                                vy = self.readU8()
                                vz = self.readU8()
                                vw = self.readU8()
                                meshinfo.tangent.append((vx/127.5-1,vy/127.5-1,vz/127.5-1,vw/127.5-1))
                else:
                    vertSize = vertexCnt*stride
                    self.seek(vbstart)
                    vb = self.__lmfile.read(vertSize)
                    hasuv = 'UV' in meshinfo.vertexDecl.vertele
                    uvoff=0 if not hasuv else  meshinfo.vertexDecl.vertele['UV'][0]

                    hasnormal = 'NORMAL' in meshinfo.vertexDecl.vertele
                    normaloff= 0 if not hasnormal else meshinfo.vertexDecl.vertele['NORMAL'][0]

                    hascolor= 'COLOR' in meshinfo.vertexDecl.vertele
                    coloroff=0 if not hascolor else meshinfo.vertexDecl.vertele['COLOR'][0]

                    hastangent='TANGENT' in meshinfo.vertexDecl.vertele
                    tangentoff=0 if not hastangent else meshinfo.vertexDecl.vertele['TANGENT'][0]

                    hasweight='BLENDWEIGHT' in meshinfo.vertexDecl.vertele
                    weightoff = 0 if not hasweight else meshinfo.vertexDecl.vertele['BLENDWEIGHT'][0]

                    hasbboneidx = 'BLENDINDICES' in meshinfo.vertexDecl.vertele
                    boneidxoff = 0 if not hasbboneidx else meshinfo.vertexDecl.vertele['BLENDINDICES'][0]
                    
                    for v in range(vertexCnt):
                        start = v*stride
                        vert = struct.unpack_from("fff", vb, start)
                        meshinfo.vb.append(vert)

                        if(hasuv):
                            uv = struct.unpack_from('ff',vb,start+uvoff)
                            meshinfo.uv0.append(uv)

                        if(hasnormal):
                            norm = struct.unpack_from('fff',vb, start+normaloff)
                            meshinfo.normal.append(norm)
                        
                        if(hascolor):
                            color = struct.unpack_from('ffff', vb, start+coloroff)
                            meshinfo.color.append(color)

                        if(hastangent):
                            tangent = struct.unpack_from('ffff',vb, start+tangentoff)
                            meshinfo.tangent.append(tangent)
                        if(hasweight):
                            weight = struct.unpack_from('ffff', vb, start+weightoff)
                            meshinfo.boneweight.append(weight)
                        if(hasbboneidx):
                            idx = struct.unpack_from('BBBB',vb,start+boneidxoff)
                            meshinfo.boneidx.append(idx)
                        
                    #假设读完了
                    self.seek(vbstart+vertSize)
                    pass
            #读ib
            self.seek(ibstart)
            ib = self.__lmfile.read(iblen)
            if(shortIB):
                for f in range(int(ibCnt/3)):
                    face = struct.unpack_from('HHH',ib,f*3*2)
                    meshinfo.ib.append((face[0],face[2],face[1]))   # 这个顺序效果好一些，具体不明
            else:
                for f in range(int(ibCnt/3)):
                    face = struct.unpack_from('III',ib,f*3*4)
                    meshinfo.ib.append((face[0],face[2],face[1]))   # 这个顺序效果好一些，具体不明
                    #meshinfo.ib.append(face)
            
            self.seek(ibstart+iblen)

            # bindpose是4x4的矩阵
            self.seek(meshinfo.data.off+bindPoseStart)
            bindpose = self.__lmfile.read(bindPoseLen)
            #假设读完了
            self.seek(meshinfo.data.off+bindPoseStart+bindPoseLen)
            pass
        pass

    def readIdxString(self,meshinfo:Mesh):
        return meshinfo.strings[self.readU16()]

    def READ_SUBMESH(self,meshinfo:Mesh):        
        '''
        每个submesh块描述一个submesh，submesh对应lh中的相应的一个材质，本来只有ibstart和ibcount，
        后来由于skin动画的限制，又把submesh拆分成了多个，称为drawcount
        '''
        unk = self.readU16()
        ibStart = self.readU32()
        ibCnt = self.readU32()
        drawCnt = self.readU16()
        submesh = SubMesh(ibStart,ibCnt)
        meshinfo.subMesh.append(submesh)
        for i in range(drawCnt):
            ibstart = self.readU32()
            ibcnt = self.readU32()
            bonedicoffs = self.readU32()
            bonediccnt = self.readU32()
        pass
    def READ_UVSIZE(self, meshinfo:Mesh):
        pass

    def READ_SKININFO(self,meshinfo:Mesh):
        normCount = self.readU16()
        skininfo = []
        for i in range(normCount):
            skininfo.append(self.readU32())
        pass

    def export(self,file:str):
        pass

##test
if __name__ == "__main__":
    # bb = [o for o in range(1,10) if o %2==0]
    # pass
    ff = LMFile()
    #ff.parse('D:/work/layaimpexp/test/muzhalan.lm')
    ff.parse('D:/work/layaimpexp/test/tifa/Mesh/mesh_null_95.lm')
    #ff.parse('D:/work/air3_layame/LayaMetaX/dist/res/layaverse/ceshi/shinei/shinei.lm')
    pass