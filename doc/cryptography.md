On the Cryptography in Fyuneru
==============================

This article will discuss how cryptography is being used in our program
Fyuneru.

In Fyuneru, one of the most important tasks is the protection of data packets
we have got and to put into the virtual network interface. Such packets are
encrypted and authenticated before its been send over a proxy, and is
authenticated before decrypted after received from a proxy. The encryption
is independent of the proxy protocol.

Encryption is based on simple symmetric keys. Therefore anyone who wants to
deploy a private proxy server, should use SSH or similar relative trustful
means to send its symmetric key to the server. The reason why not using an
asymmetric method for negotiating a key is, that:

    1) This cannot guarentee more security if the server we are using as proxy
       is not secure.
    2) That we want to use construct such ciphertexts, that it has no more
       characteristics as its length. It has to appear as pseudo-random. No
       flag bits, no plaintexts...

The encryption schema is shown as following diagram:

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

Each raw plaintext buffer being encrypted has a length of no more than
    
    0xFFFF - 20 - 24 - 2 = 65489 bytes

0xFFFF is the maximal length of a UDP packet, which is being used in our
program as intermediate packets between core and proxies. 20 for a SHA1-HMAC
result and 24 for an IV, 2 for the length recording in cleartext.

Random padding can be applied in the cleartext, to conceal the real length
of the buffer.

We use **HMAC-SHA1** to authenticate the **encrypted buffer** instead of
plaintext in following reasons:

    1. A good HMAC should be indistinguishable against random bytes without
       knowledge of key. Putting it outside the cleartext and making it to
       authenticate the cihpertext makes it easier(with a known HMAC key!) to
       find out invalid packets without decryption.

    2. This is secure enough. SHA1 is attacked only in theory, and that's even
       not HMAC(HMAC-MD5 is still secure enough, think of that). Even an
       attacker has got some advances in theory, it doesn't mean he will be
       able to use it detecting a real-time traffic effectively(making it hard
       to do deep packet analysis).
    3. HMAC-SHA1 is 12 bytes shorter as SHA256 or more secure hash algorithms.

Unrevealing the HMAC key will not lead to the leak of encryption key, since the
HMAC key is derived from encryption key. If however someone has got this key,
he will be able to trick our program with seemingly legal traffic, and he
cannot distinguish or get a proof, that it is us not him that has sent
anything.

We use **XSalsa20** to encrypt the buffer. XSalsa20 is a stream cipher, and
this is good since it will produce the same bytes of output as the cleartext,
block ciphers will make bytes always multiples of some 16 or 32 bytes, which
makes it distinguishable against a carefully observer.
