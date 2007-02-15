#!/usr/bin/env python
"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

import base64, hashlib
from M2Crypto import X509, RSA
from lxml import etree

class CertificateCheckFailed(ValueError):
    pass

class PrivateKeyCheckFailed(ValueError):
    pass

class ValidationError(ValueError):
    pass


class X509Certificate(object):
    """This class wraps around the M2Crypto.X509 class."""

    def __init__(self, m2_x509, priv_key=None):
        """Initialize a X.509 certificate using a M2Crypto X509 instance.

        if priv_key is given, too, this class may be used to sign/encrypt data.
        """
        if not isinstance(m2_x509, X509.X509):
            raise CertificateCheckFailed("certificate must be a M2Crypto.X509 instance")
        self.__x509 = m2_x509
        self.__pub_key = RSA.RSA_pub(m2_x509.get_pubkey().get_rsa().rsa)

        if priv_key and not isinstance(priv_key, RSA.RSA):
            raise KeyCheckFailed("the private key must be a M2Crypto.RSA instance.")
        self.__priv_key = priv_key

    def pub_key(self):
        return self.__pub_key

    def priv_key(self):
        return self.__priv_key

    def __default_digest(data, algo):
        hash_func = hashlib.new(algo)
        hash_func.update(data)
        return hash_func.digest()

    # some convenience functions
    def msg_signature(self, data, algo="sha1", digest=__default_digest):
        """generate a base64 encoded message signature of data.

        data -- the data to be signed
        algo -- the algorithm to compute the digest of data
        digest -- a callable that shall be used as the digest generator
                  it is called as: digest(data, algo)
                  if None (default) the hashlib is used to get an algorithm
        """
        if self.priv_key() is None:
            raise RuntimeError("signing requires a private key, sorry.")
        
        # compute the digest out of the data
        _dgst = digest(data, algo)
        # sign the  digest with the  stored key and return  the base64
        # encoded result
        return base64.b64encode(self.priv_key().sign(_dgst, algo))

    def msg_validate(self, data, signature, algo="sha1", digest=__default_digest):
        """validate the given data with the provided signature.

        data -- the data to be validated
        signature -- the provided signature
        algo -- the algorithm that was used to compute signature
        digest -- a callable that shall be used as the digest generator
                  it is called as: digest(data, algo)
                  if None (default) the hashlib is used to get an algorithm

        in this case the 'source certificate' is used.
        """
        dec_signature = base64.b64decode(signature)
        _dgst = digest(data, algo)
        try:
            self.pub_key().verify(_dgst, dec_signature, algo)
        except RSA.RSAError, ra:
            raise ValidationError("the given data did not match the signature!")
        return True

    def msg_encrypt(self, data, encode=True):
        """return the base64 encoded encryption of 'data'.

        if encode is True (default), return the value in base64 encoding.
        """
        cipher = self.pub_key().public_encrypt(data, 1)
        if encode: cipher = base64.b64encode(cipher)
        return cipher

    def msg_decrypt(self, cipher, decode=True):
        """return the decrypted value of the cipher.

        if decode is True (default), asume that cipher is base64
        encoded and decode it first.
        """
        if self.priv_key() is None:
            raise RuntimeError("decryption requires a private key, sorry.")
        if decode: cipher = base64.b64decode(cipher)
        return self.priv_key().private_decrypt(cipher, 1)

    def load(cls, crt, key_string=None):
        x509 = X509.load_cert_string(crt)
        key = key_string and RSA.load_key_string(key_string)
        return cls(x509, key)
    load = classmethod(load)

    def load_from_files(cls, crt_path, key_path=None):
        """Loads the certificate from the given files.

        crt_path - points to the file containing the X509 certificate
        key_path - if not None points to the file containing the RSA private key
        """
        x509 = X509.load_cert(crt_path)
        key = key_path and RSA.load_key(key_path)
        return cls(x509, key)
    load_from_files = classmethod(load_from_files)
    
class CertificateStore(object):
    """
    Holds needed keys and certificates for the desired operations.

    For encryption it must hold:
         * sender certificate + private key (for signing)
         * receiver certificate

    For decryption it must hold:
         * sender certificate (for validation)
         * receiver certificate + private key (for decryption)

    The information is kept in generic placeholders, so that the
    SecurityPipe may refer to them uniformly.

    And of course the CA-certificate for validation.
    """
    
    def __init__(self, src_cert, dst_cert, key, ca_certs=[]):
        self.__src_crt = src_cert
        self.__dst_crt = dst_cert
        self.__ca_crts = []
        self.__ca_crts.extend(ca_certs)

    def src_cert(self):
        return self.__src_crt
    def dst_cert(self):
        return self.__dst_crt
