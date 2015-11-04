"""
Cryptographical Services
========================

## Authenticator in IPC communication

In IPC communications, data are not encrypted, but it has to be authenticated
since any process can practically send data to a UDP port our process listening
on. We currently use HMAC-MD5, for local usage this should be enough and
performance comes first.


## Encryption and Decryption for Internet Traffic

### Schema

    1. Cleartext:
                          | BUFFER arbitary length |
                | DATALEN |                        | RANDOM PADDING |
     Bytes      |  2      | ?                      | ?              |

    2. Encryption:
                       | ENCRYPTED BUFFER ................................ |
           | IV | HMAC |
     Bytes | 24 |  20  |                                                   |

    3. Result:
           | PSEUDORANDOM BUFFER OF RANDOM LENGTH ........................ |
     Bytes | ?                                                             |

### Remarks

1. We use HMAC-SHA1 to authenticate the encrypted buffer in following reasons:
1.1 A good HMAC should be indistinguishable against random bytes without
    knowledge of key. Putting it outside the cleartext and making it to
    authenticate the cihpertext makes it easier(with a known HMAC key!) to find
    out invalid packets without decryption.
1.2 This is secure enough. SHA1 is attacked only in theory, and that's even not
    HMAC(HMAC-MD5 is still secure enough, think of that). Even an attacker has
    got some advances in theory, it doesn't mean he will be able to use it
    detecting a real-time traffic effectively(making it hard to do deep packet
    analysis).
1.3 Unrevealing the HMAC key will not lead to the leak of encryption key, since 
    the HMAC key is derived from encryption key. If however someone has got
    this key, he will be able to trick our program with seemingly legal
    traffic, and he cannot distinguish or get a proof, that it is us not him
    that has sent anything.
1.4 HMAC-SHA1 is 12 bytes shorter as SHA256.

"""

import hashlib 
import hmac
import math
from os import urandom
from struct import pack, unpack

from salsa20 import XSalsa20_xor

_HASHALGO = hashlib.sha1
_HASHLEN = len(_HASHALGO('').digest())

_RESULT_SIZE = 0xFFFF - 24 - 2 - _HASHLEN 


class CryptoException(Exception): pass

def randint(a, b):
    i = unpack('<L', urandom(4))[0]
    return a + i % (b-a+1)

def randrange(a, b):
    i = unpack('<L', urandom(4))[0]
    return a + i % (b-a)

def decidePaddingLength(bufferLength):
    global _RESULT_SIZE
    return 0
    if bufferLength < 1500:
        randSize = randint(0, 1500)
        if randSize > bufferLength:
            return randSize - bufferLength
        return 0
    else:
        maxSize = int(min(_RESULT_SIZE - bufferLength, bufferLength * 2.0))
        return randint(0, maxSize)

def KDF1(secret, length):
    """ISO-18033-2 defined simple KDF function. Notice we assume secret is
    already long and random enough."""
    global _HASHALGO, _HASHLEN
    d = int(math.ceil(length * 1.0 / _HASHLEN))
    T = ""
    for i in xrange(0, d):
        C = pack("<H", i)
        T = T + _HASHALGO(secret + C).digest()
    return T[:length]
KDF = KDF1

##############################################################################

class Authenticator:
    """Authentication service for IPC mechanism. Provides signing and
    verifying.  For signing a buffer, the HMAC result will be returned together
    with original buffer.  This result can then be passed to the verify
    function on another process. If verification succeeded, return buffer. If
    not, return None."""

    __ALGORITHM_CONFIG = (hashlib.md5, 16) # 16 bytes output for MD5.

    def __init__(self, key):
        self.__origHMAC = hmac.new(key, '', self.__ALGORITHM_CONFIG[0])

    def __HMAC(self, buf):
        worker = self.__origHMAC.copy()
        worker.update(buf)
        return worker.digest()

    def sign(self, buf):
        signature = self.__HMAC(buf)
        return signature + buf

    def verify(self, buf):
        hlen = self.__ALGORITHM_CONFIG[1]
        if len(buf) < hlen: return None
        signature = buf[:hlen]
        buf = buf[hlen:]
        if self.__HMAC(buf) != signature: return None
        return buf



class Crypto:
    """Crypto service for traffic over Internet."""

    def __init__(self, passphrase):
        self.__KEY = KDF(passphrase, 32)
        HMACKEY = KDF(self.__KEY, _HASHLEN)
        self.__origHMAC = hmac.new(HMACKEY, '', _HASHALGO)

    def __HMAC(self, buf):
        worker = self.__origHMAC.copy()
        worker.update(buf)
        return worker.digest()

    def encrypt(self, buf):
        if len(buf) > _RESULT_SIZE: 
            raise CryptoException('Buffer too large to be encrypted.')

        buflen = len(buf)
        lenstr = pack('<H', buflen)
        padding = '0' * decidePaddingLength(buflen) # TODO discuss security here!
        cleartext = lenstr + buf + padding

        iv = urandom(24) # since IV will be exposed, has to be crypto. random.
        ciphertext = XSalsa20_xor(cleartext, iv, self.__KEY)
        hmac = self.__HMAC(ciphertext)

        return iv + hmac + ciphertext

    def decrypt(self, buf):
        if len(buf) < 24 + _HASHLEN:
            return False
        iv = buf[:24]
        hmac = buf[24:24+_HASHLEN]
        ciphertext = buf[24+_HASHLEN:]

        hmac2 = self.__HMAC(ciphertext)
        if hmac2 != hmac: return False

        decrypted = XSalsa20_xor(ciphertext, iv, self.__KEY)
        lenstr = decrypted[:2]
        buflen = unpack('<H', lenstr)[0]
        buf = decrypted[2:][:buflen]
        if len(buf) != buflen: return False
        
        return buf


if __name__ == '__main__':
    encryptor = Crypto('test')
    decryptor = Crypto('test')

    import time
    a = time.time()
    for x in xrange(0, 1024):
        encrypted = encryptor.encrypt('a' * 400)
        decrypted = encryptor.decrypt(encrypted)
        if not decrypted:
            print "*"
    b = time.time()
    print "done in %f seconds" % (b-a)
#    print len(encrypted), decryptor.decrypt(encrypted)
