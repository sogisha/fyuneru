import hashlib 
import hmac
from os import urandom

from salsa20 import XSalsa20_xor

_HASHALGO = hashlib.sha256
_HASHLEN = len(_HASHALGO('').digest())

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
        hmac = self.__HMAC(buf)
        iv = urandom(24) # since IV will be exposed, has to be crypto. random.
        cleartext = hmac + buf
        encrypted = XSalsa20_xor(cleartext, iv, self.__KEY)
        return iv + encrypted

    def decrypt(self, buf):
        if len(buf) < 24:
            return False
        iv = buf[:24]
        ciphertext = buf[24:]
        decrypted = XSalsa20_xor(ciphertext, iv, self.__KEY)
        hmac = decrypted[:_HASHLEN]
        buf = decrypted[_HASHLEN:]
        if self.__HMAC(buf) != hmac:
            return False
        return buf
