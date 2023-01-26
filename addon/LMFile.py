import os
import struct

class ChunkInfo:
    def __init__(self,off=0,size=0) -> None:
        self.off=off
        self.size=size

class MeshInfo:
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


    def parse(self, fileName:str)->MeshInfo:
        self.__lmfile = open(fileName,"rb")
        self.__lmfile.seek(0, os.SEEK_END)
        self.__fileSize = self.__lmfile.tell()
        self.__lmfile.seek(0, os.SEEK_SET)
        meshinfo = MeshInfo()
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

        return meshinfo

    def parsev05NoComp(self,off:int):
        pass

    def getVertexElementSize(self,type:str):
        dict = {"POSITION":12,"NORMAL":12,"COLOR":16,"UV":8,"UV1":8,"BLENDWEIGHT":16,"BLENDINDICES":4,"TANGENT":16,"NORMAL_BYTE":4}
        return dict[type]

    def READ_MESH(self,meshinfo:MeshInfo):
        strings = meshinfo.strings
        name= strings[self.readU16()]
        vbcount = self.readU16()
        dataoff =  meshinfo.data.off
        for i in range(vbcount):
            vbstart = dataoff+self.readU32()
            vertexCnt = self.readU32()
            shortIB=True
            if(vertexCnt>65535):
                shortIB=False

            vertexFlags = self.readIdxString(meshinfo)
            flags = str.split(vertexFlags,',')
            stride=0
            for j in flags:
                stride+=self.getVertexElementSize(j)

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
            if meshinfo.isV05 and not meshinfo.isCompress:
                vertSize = vertexCnt*stride
                self.seek(vbstart)
                vb = self.__lmfile.read(vertSize)
                for v in range(vertexCnt):
                    vert = struct.unpack_from("fff", vb, v*stride)
                    meshinfo.vb.append(vert)
                #假设读完了
                self.seek(vbstart+vertSize)
                pass
            if meshinfo.isCompress:
                return RuntimeError()
                pass

            #读ib
            self.seek(ibstart)
            ib = self.__lmfile.read(iblen)
            if(shortIB):
                for f in range(int(ibCnt/3)):
                    face = struct.unpack_from('HHH',ib,f*3*2)
                    meshinfo.ib.append(face)
            else:
                for f in range(int(ibCnt/3)):
                    face = struct.unpack_from('HHH',ib,f*3*4)
                    meshinfo.ib.append(face)
            
            self.seek(ibstart+iblen)

            # bindpose是4x4的矩阵
            self.seek(meshinfo.data.off+bindPoseStart)
            bindpose = self.__lmfile.read(bindPoseLen)
            #假设读完了
            self.seek(meshinfo.data.off+bindPoseStart+bindPoseLen)
            pass
        pass

    def readIdxString(self,meshinfo:MeshInfo):
        return meshinfo.strings[self.readU16()]

    def READ_SUBMESH(self,meshinfo:MeshInfo):        
        unk = self.readU16()
        ibStart = self.readU32()
        ibCnt = self.readU32()
        drawCnt = self.readU16()
        for i in range(drawCnt):
            ibstart = self.readU32()
            ibcnt = self.readU32()
            bonedicoffs = self.readU32()
            bonediccnt = self.readU32()
        pass
    def READ_UVSIZE(self, meshinfo:MeshInfo):
        pass

##test
if __name__ == "__main__":
    ff = LMFile()
    ff.parse('D:/work/layaimpexp/test/femalezhenghe-female0.lm')
    pass