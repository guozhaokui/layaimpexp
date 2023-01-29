import struct
import binascii

class Float16Compressor:
    def __init__(self):
        self.temp = 0

    def compress(self,float32:float):
        F16_EXPONENT_BITS = 0x1F
        F16_EXPONENT_SHIFT = 10
        F16_EXPONENT_BIAS = 15
        F16_MANTISSA_BITS = 0x3ff
        F16_MANTISSA_SHIFT =  (23 - F16_EXPONENT_SHIFT)
        F16_MAX_EXPONENT =  (F16_EXPONENT_BITS << F16_EXPONENT_SHIFT)

        a = struct.pack('>f',float32)
        b = binascii.hexlify(a)

        f32 = int(b,16)
        f16 = 0
        sign = (f32 >> 16) & 0x8000
        exponent = ((f32 >> 23) & 0xff) - 127
        mantissa = f32 & 0x007fffff

        if exponent == 128:
            f16 = sign | F16_MAX_EXPONENT
            if mantissa:
                f16 |= (mantissa & F16_MANTISSA_BITS)
        elif exponent > 15:
            f16 = sign | F16_MAX_EXPONENT
        elif exponent > -15:
            exponent += F16_EXPONENT_BIAS
            mantissa >>= F16_MANTISSA_SHIFT
            f16 = sign | exponent << F16_EXPONENT_SHIFT | mantissa
        else:
            f16 = sign
        return f16

    def decompress(self,float16:int):
        s = int((float16 >> 15) & 0x00000001)    # sign
        e = int((float16 >> 10) & 0x0000001f)    # exponent
        f = int(float16 & 0x000003ff)            # fraction

        if e == 0:
            if f == 0:
                return int(s << 31)
            else:
                while not (f & 0x00000400):
                    f = f << 1
                    e -= 1
                e += 1
                f &= ~0x00000400
                #print(s,e,f)
        elif e == 31:
            if f == 0:
                return int((s << 31) | 0x7f800000)
            else:
                return int((s << 31) | 0x7f800000 | (f << 13))

        e = e + (127 -15)
        f = f << 13
        r = int((s << 31) | (e << 23) | f)
        str = struct.pack('I',r)
        return struct.unpack('f',str)[0]


class HalfFloatUtils:
    _baseTable=[0]*512
    _shiftTable=[0]*512
    _mantissaTable=[0]*2048
    _exponentTable=[0]*64
    _offsetTable=[0]*64
    _inited=False

    def __init__(self):
        if not HalfFloatUtils._inited:
            HalfFloatUtils._inited=True
            for i in range(256):
                e=i-127
                # very small number (0, -0)
                if (e < -27):
                    HalfFloatUtils._baseTable[i | 0x000] = 0x0000
                    HalfFloatUtils._baseTable[i | 0x100] = 0x8000
                    HalfFloatUtils._shiftTable[i | 0x000] = 24
                    HalfFloatUtils._shiftTable[i | 0x100] = 24
                elif( e<-14):
                    HalfFloatUtils._baseTable[i | 0x000] = 0x0400 >> (-e - 14)
                    HalfFloatUtils._baseTable[i | 0x100] = (0x0400 >> (-e - 14)) | 0x8000
                    HalfFloatUtils._shiftTable[i | 0x000] = -e - 1
                    HalfFloatUtils._shiftTable[i | 0x100] = -e - 1
                elif(e<=15):
                    HalfFloatUtils._baseTable[i | 0x000] = (e + 15) << 10
                    HalfFloatUtils._baseTable[i | 0x100] = ((e + 15) << 10) | 0x8000
                    HalfFloatUtils._shiftTable[i | 0x000] = 13
                    HalfFloatUtils._shiftTable[i | 0x100] = 13
                    # large number (Infinity, -Infinity)
                elif(e<128):
                    HalfFloatUtils._baseTable[i | 0x000] = 0x7c00
                    HalfFloatUtils._baseTable[i | 0x100] = 0xfc00
                    HalfFloatUtils._shiftTable[i | 0x000] = 24
                    HalfFloatUtils._shiftTable[i | 0x100] = 24
                    # stay (NaN, Infinity, -Infinity)
                else:
                    HalfFloatUtils._baseTable[i | 0x000] = 0x7c00
                    HalfFloatUtils._baseTable[i | 0x100] = 0xfc00
                    HalfFloatUtils._shiftTable[i | 0x000] = 13
                    HalfFloatUtils._shiftTable[i | 0x100] = 13

            HalfFloatUtils._mantissaTable[0]=0
            for i in range(1,1024):
                m=i<<13 #zero pad mantissa bits
                e = 0;          # zero exponent
                #normalized
                while (m & 0x00800000) == 0:
                    e -= 0x00800000;    # decrement exponent
                    m <<= 1
                m &= ~0x00800000;   # clear leading 1 bit
                e += 0x38800000;    # adjust bias
                HalfFloatUtils._mantissaTable[i] = m | e
                
            for i in range(1024,2048):
                HalfFloatUtils._mantissaTable[i] = 0x38000000 + ((i - 1024) << 13)

            HalfFloatUtils._exponentTable[0] = 0
            for i in range(1,31):
                HalfFloatUtils._exponentTable[i] = i << 23
            HalfFloatUtils._exponentTable[31] = 0x47800000
            HalfFloatUtils._exponentTable[32] = 0x80000000            

            for i in range(33,63):
                HalfFloatUtils._exponentTable[i] = 0x80000000 + ((i - 32) << 23)
            HalfFloatUtils._exponentTable[63] = 0xc7800000

            HalfFloatUtils._offsetTable[0] = 0
            for i in range(1,64):
                if i==32:
                    HalfFloatUtils._offsetTable[i] = 0
                else:
                    HalfFloatUtils._offsetTable[i] = 1024

    def roundToFloat16Bits(self,v:float):
        b = struct.pack('f',v)
        iv = struct.unpack('I',b)[0]
        e = (iv >> 23) & 0x1ff
        r = HalfFloatUtils._baseTable[e] + ((iv & 0x007fffff) >> HalfFloatUtils._shiftTable[e])
        return r

    def convertToNumber(self,f16:int):
        m = f16>>10
        v = HalfFloatUtils._mantissaTable[HalfFloatUtils._offsetTable[m] + (f16 & 0x3ff)] + HalfFloatUtils._exponentTable[m]
        str = struct.pack('I',v)
        r = struct.unpack('f',str)[0]
        return r

##test
if __name__ == "__main__":
    
    f16 = HalfFloatUtils()
    r = f16.roundToFloat16Bits(-110.21)
    r1 = f16.convertToNumber(r)
    pass
