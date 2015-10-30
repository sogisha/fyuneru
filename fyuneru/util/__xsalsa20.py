"""
XSalsa20 Cipher Implementation in Pure Python
=============================================

This library provides a pure python implementation of XSalsa20 cipher.

NOTICE! This cipher uses only lower 32 bits of counter, since the higher bits
cannot be used in our fyuneru system(we just encrypt buffer no larger than
65536 bytes=1024 blocks).
"""

import array
import math

uintArray = lambda l: array.array('I', [0] * l)


class XSalsa20:
    
    def __salsa20Core(self, uintArray16):
        x = self.__x
        x[:] = uintArray16[:]
        R = lambda a,b: (((a) << (b)) | ((a) >> (32 - (b)))) & 0xFFFFFFFF 
        for i in xrange(0, 10): # half of r(=20), r/2 rounds
            x[ 4] ^= R(x[ 0]+x[12], 7)
            x[ 8] ^= R(x[ 4]+x[ 0], 9)
            x[12] ^= R(x[ 8]+x[ 4],13)
            x[ 0] ^= R(x[12]+x[ 8],18)
            x[ 9] ^= R(x[ 5]+x[ 1], 7)
            x[13] ^= R(x[ 9]+x[ 5], 9)
            x[ 1] ^= R(x[13]+x[ 9],13)
            x[ 5] ^= R(x[ 1]+x[13],18)
            x[14] ^= R(x[10]+x[ 6], 7)
            x[ 2] ^= R(x[14]+x[10], 9)
            x[ 6] ^= R(x[ 2]+x[14],13)
            x[10] ^= R(x[ 6]+x[ 2],18)
            x[ 3] ^= R(x[15]+x[11], 7)
            x[ 7] ^= R(x[ 3]+x[15], 9)
            x[11] ^= R(x[ 7]+x[ 3],13)
            x[15] ^= R(x[11]+x[ 7],18)
            x[ 1] ^= R(x[ 0]+x[ 3], 7)
            x[ 2] ^= R(x[ 1]+x[ 0], 9)
            x[ 3] ^= R(x[ 2]+x[ 1],13)
            x[ 0] ^= R(x[ 3]+x[ 2],18)
            x[ 6] ^= R(x[ 5]+x[ 4], 7)
            x[ 7] ^= R(x[ 6]+x[ 5], 9)
            x[ 4] ^= R(x[ 7]+x[ 6],13)
            x[ 5] ^= R(x[ 4]+x[ 7],18)
            x[11] ^= R(x[10]+x[ 9], 7)
            x[ 8] ^= R(x[11]+x[10], 9)
            x[ 9] ^= R(x[ 8]+x[11],13)
            x[10] ^= R(x[ 9]+x[ 8],18)
            x[12] ^= R(x[15]+x[14], 7)
            x[13] ^= R(x[12]+x[15], 9)
            x[14] ^= R(x[13]+x[12],13)
            x[15] ^= R(x[14]+x[13],18)
        for i in xrange(0, 16):
            uintArray16[i] = (uintArray16[i] + x[i]) & 0xFFFFFFFF

    def __streamXor(self, iv, key, buf):
        c2u = lambda src, f:\
            src[f] + (src[f+1] << 4) + (src[f+2] << 8) + (src[f+3] << 12)
        key = bytearray(key)
        iv = bytearray(iv)
        len0 = len(buf)
        buf = bytearray(buf) + bytearray('0' * 64)

        if len(key) != 32 or len(iv) != 24:
            raise Exception("Key must be 32 bytes, IV must be 24 bytes")

        bkX = uintArray(16)
        bkX[0], bkX[5], bkX[10], bkX[15] =\
            0x61707865, 0x3320646e, 0x79622d32, 0x6b206574
        bkX[1], bkX[2], bkX[3], bkX[4] = \
            c2u(key, 0), c2u(key, 4), c2u(key, 8), c2u(key, 12)
        bkX[11], bkX[12], bkX[13], bkX[14] = \
            c2u(key, 16), c2u(key, 20), c2u(key, 24), c2u(key, 28)
        bkX[6], bkX[7], bkX[8], bkX[9] = \
            c2u(iv, 0), c2u(iv, 4), c2u(iv, 8), c2u(iv, 12)

        # XSalsa20/r computes (z0,z1,...,z15) = doubleround^r/2(x0,x1,...x15).
        self.__salsa20Core(bkX)
        # It then builds a new 512-bit input block (x0',x1',...,x15'),...
        bkY = uintArray(16)
        bkY[0], bkY[5], bkY[10], bkY[15] =\
            0x61707865, 0x3320646e, 0x79622d32, 0x6b206574
        bkY[1], bkY[2], bkY[3], bkY[4] = bkX[0], bkX[5], bkX[10], bkX[15]
        bkY[11], bkY[12], bkY[13], bkY[14] = bkX[6], bkX[7], bkX[8], bkX[9]
        bkY[6], bkY[7] = c2u(iv, 16), c2u(iv, 20) # ...last 64 bits of the 192-bit nonce
        bkY[8] = 0 # higher bits of counter, we don't need them

        counter0 = 0
        i = 0
        output = bytearray('0' * (len0 + 64))
        while i < len0:
            bkY[9] = counter0
            self.__salsa20Core(bkY)
            for j in xrange(0, 16):
                output[i+0] = buf[i+0] ^ ((bkY[j] & 0x000000FF))
                output[i+1] = buf[i+1] ^ ((bkY[j] & 0x0000FF00) >> 8)
                output[i+2] = buf[i+2] ^ ((bkY[j] & 0x00FF0000) >> 16)
                output[i+3] = buf[i+3] ^ ((bkY[j] & 0xFF000000) >> 24)
                i += 4
            counter0 += 1
        return str(output[:len0])

    def __init__(self):
        self.__x = uintArray(16)

    def encrypt(self, iv, key, buf):
        return self.__streamXor(iv, key, buf)

    def decrypt(self, iv, key, buf):
        return self.__streamXor(iv, key, buf)


if __name__ == "__main__":
    key = bytearray('0' * 32)
    iv = bytearray('1' * 24)
    buf = 'test' * 400 
    c = XSalsa20()

    import time
    a = time.time()
    for i in xrange(0, 100):
        enc = c.encrypt(iv, key, buf)
        dec = c.decrypt(iv, key, enc)
    b = time.time()
    print dec == buf
    print (100 * 400 * 4.0) / (b-a)
