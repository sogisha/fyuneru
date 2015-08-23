import hashlib 
import hmac
from os import urandom

from salsa20 import XSalsa20_xor

from _config import config

"""
KEY = hashlib.pbkdf2_hmac(\
    "sha256",
    config["KEY"],
    "Encryption-Key",
    config["PBKDF2_ITERATION"],
    32
)

HMACKEY = hashlib.pbkdf2_hmac(\
    "sha256",
    config["KEY"],
    "Verification-Key",
    config["PBKDF2_ITERATION"],
    64
)
"""
KEY = hashlib.sha256(config["KEY"]).digest()
HMACKEY = hashlib.sha256(KEY).digest()
KEY = KEY[:32]

_HMACALGO = hashlib.sha256
_HMACLEN = len(_HMACALGO('').digest())
_origHMAC = hmac.new(HMACKEY, '', _HMACALGO)
def HMAC(buf):
    global _origHMAC
    worker = _origHMAC.copy()
    worker.update(buf)
    return worker.digest()


def encrypt(buf):
    global KEY
    hmac = HMAC(buf)
    iv = urandom(24) # since IV will be exposed, has to be crypto. random.
    cleartext = hmac + buf
    encrypted = XSalsa20_xor(cleartext, iv, KEY)
    return iv + encrypted

def decrypt(buf):
    global KEY, _HMACLEN
    if len(buf) < 24:
        return False
    iv = buf[:24]
    ciphertext = buf[24:]
    decrypted = XSalsa20_xor(ciphertext, iv, KEY)
    hmac = decrypted[:_HMACLEN]
    buf = decrypted[_HMACLEN:]
    if HMAC(buf) != hmac:
        return False
    return buf
