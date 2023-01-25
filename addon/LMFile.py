import os
import struct

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

    def readString(self):
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

    def parse(self, fileName):
        self.__lmfile = open(fileName,"rb")
        self.__lmfile.seek(0, os.SEEK_END)
        self.__fileSize = self.__lmfile.tell()
        self.__lmfile.seek(0, os.SEEK_SET)


##test
if __name__ == "__main__":
    ff = LMFile()
    ff.parse('D:/work/layaimpexp/test/muzhalan.lm')