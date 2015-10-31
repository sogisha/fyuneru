"""
Modified XSalsa20/16 Cipher Implementation in Pure Python
======================================================

This library provides a pure python implementation of XSalsa20/16 cipher.

This library is a modification of XSalsa20 cipher and adapted for fyuneru.
Changed is merely the nonce length from 24 bytes to 28 bytes. The extra 4 bytes
are given as higher 32 bits of the counter, making the counter only able
to count with 32 bits. Since our usage of this cipher uses a different nonce
for each plaintext being encrypted, but each plaintext will not be more than
65536 bytes(describable with just 2 bytes), this is better suited.

This implementation is not audited and may have errors that lead to serious
problems. And it's slow. 
"""

import array
import math

uintArray = lambda l: array.array('I', [0] * l)
uintArray = lambda l: [0] * l 


class XSalsa20:
    
    def __salsa20Core(self, x, inbuf, oubuf):
        for i in xrange(0, 16): x[i] = inbuf[i]
        R = lambda a,b: (((a) << (b)) | ((a) >> (32 - (b)))) & 0xFFFFFFFF 
        for i in xrange(0, 8): # half of r(=16), r/2 rounds
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
        for i in xrange(0, 16): oubuf[i] = (inbuf[i] + x[i]) & 0xFFFFFFFF

    def __streamXor(self, iv, key, buf):
        c2u = lambda src, f:\
            src[f] + (src[f+1] << 4) + (src[f+2] << 8) + (src[f+3] << 12)
        key = bytearray(key)
        iv = bytearray(iv)
        len0 = len(buf)
        buf = bytearray(buf) + bytearray('0' * 64)

        if len(key) != 32 or len(iv) != 28:
            raise Exception("Key must be 32 bytes, IV must be 28 bytes")

        temp = uintArray(16)
        b1i, b1o = uintArray(16), uintArray(16)
        b2i, b2o = uintArray(16), uintArray(16)
        salsa20Constants = (0x61707865, 0x3320646e, 0x79622d32, 0x6b206574)

        b1i[0], b1i[5], b1i[10], b1i[15] = salsa20Constants
        b1i[1], b1i[2], b1i[3], b1i[4] = \
            c2u(key, 0), c2u(key, 4), c2u(key, 8), c2u(key, 12)
        b1i[11], b1i[12], b1i[13], b1i[14] = \
            c2u(key, 16), c2u(key, 20), c2u(key, 24), c2u(key, 28)
        b1i[6], b1i[7], b1i[8], b1i[9] = \
            c2u(iv, 0), c2u(iv, 4), c2u(iv, 8), c2u(iv, 12)

        self.__salsa20Core(temp, b1i, b1o)

        b2i[0], b2i[5], b2i[10], b2i[15] = salsa20Constants
        b2i[1], b2i[2], b2i[3], b2i[4] = b1o[0], b1o[5], b1o[10], b1o[15]
        b2i[11], b2i[12], b2i[13], b2i[14] = b1o[6], b1o[7], b1o[8], b1o[9]
        b2i[6], b2i[7] = c2u(iv, 16), c2u(iv, 20) 
        b2i[8] = c2u(iv, 24)

        i = 0
        output = bytearray('0' * (len0 + 64))
        b2i[9] = 0
        while i < len0:
            self.__salsa20Core(temp, b2i, b2o)
            for j in xrange(0, 16):
                output[i+0] = buf[i+0] ^ ((b2o[j] & 0x000000FF))
                output[i+1] = buf[i+1] ^ ((b2o[j] & 0x0000FF00) >> 8)
                output[i+2] = buf[i+2] ^ ((b2o[j] & 0x00FF0000) >> 16)
                output[i+3] = buf[i+3] ^ ((b2o[j] & 0xFF000000) >> 24)
                i += 4
            b2i[9] += 1
        return str(output[:len0])

    def encrypt(self, iv, key, buf):
        return self.__streamXor(iv, key, buf)

    def decrypt(self, iv, key, buf):
        return self.__streamXor(iv, key, buf)


if __name__ == "__main__":
    from salsa20 import XSalsa20_xor


    key = bytearray([0] * 32)
    key[0] = 0x80
    iv  = bytearray([0] * 28)
    buf = bytearray([0] * 50)
    c = XSalsa20()
    print c.encrypt(iv, key, buf).encode('hex')
    print XSalsa20_xor(str(buf), str(iv)[:24], str(key)).encode('hex')
    exit()

    key = '0' * 32
    iv = '1' * 28
    buf = 't' * 1684 
    c = XSalsa20()
    repeat = 1000

    import time

    a = time.time()
    for i in xrange(0, repeat):
        ourres = c.encrypt(iv, key, buf)
    b = time.time()

    print len(buf) * repeat * 1.0 / (b - a)
