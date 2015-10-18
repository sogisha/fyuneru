"""
Encryption

    1. Cleartext:
                                 | BUFFER arbitary length |
                | DATALEN | HMAC |                        | RANDOM PADDING |
     Bytes      |  2      |  32  | ?                      | ?              |

    2. Encryption:
                | ENCRYPTED BUFFER ....................................... |
           | IV |
     Bytes | 24 | ?                                                        |

    3. Result:
           | PSEUDORANDOM BUFFER OF RANDOM LENGTH ........................ |
     Bytes | ?                                                             |

"""

import hashlib 
import hmac
from os import urandom
from struct import pack, unpack
import random

from salsa20 import XSalsa20_xor

_HASHALGO = hashlib.sha256
_HASHLEN = len(_HASHALGO('').digest())

_RESULT_SIZE = 0xFFFF - 24 - 2 - 32 


class CryptoException(Exception): pass

def decidePaddingLength(bufferLength):
    global _RESULT_SIZE
    minSize = 0
    if bufferLength < 1600:
        maxSize = 800 
    else:
        maxSize = int(min(_RESULT_SIZE - bufferLength, bufferLength * 2.0))
    return random.randint(minSize, maxSize)

class Crypto:
    def __init__(self, passphrase):
        KEY = _HASHALGO(passphrase).digest()
        HMACKEY = _HASHALGO(KEY).digest()
        self.__KEY = KEY[:32]
        self.__origHMAC = hmac.new(HMACKEY, '', _HASHALGO)

    def __HMAC(self, buf):
        worker = self.__origHMAC.copy()
        worker.update(buf)
        return worker.digest()

    def encrypt(self, buf):
        if len(buf) > _RESULT_SIZE: 
            raise CryptoException('Buffer too large to be encrypted.')

        hmac = self.__HMAC(buf)
        buflen = len(buf)
        lenstr = pack('<H', buflen)
        padding = '0' * decidePaddingLength(buflen) # TODO discuss security here!

        iv = urandom(24) # since IV will be exposed, has to be crypto. random.
        cleartext = lenstr + hmac + buf + padding
        encrypted = XSalsa20_xor(cleartext, iv, self.__KEY)
        return iv + encrypted

    def decrypt(self, buf):
        if len(buf) < 24:
            return False
        iv = buf[:24]
        ciphertext = buf[24:]
        decrypted = XSalsa20_xor(ciphertext, iv, self.__KEY)

        lenstr = decrypted[:2]
        buflen = unpack('<H', lenstr)[0]
        hmac = decrypted[2:_HASHLEN+2]
        buf = decrypted[_HASHLEN+2:][:buflen]
        
        if self.__HMAC(buf) != hmac:
            return False
        return buf


if __name__ == '__main__':
    encryptor = Crypto('test')
    decryptor = Crypto('test')
    encrypted = encryptor.encrypt('hello, world' * 30)
    print len(encrypted), decryptor.decrypt(encrypted)
