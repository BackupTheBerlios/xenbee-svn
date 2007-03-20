"""Security classes using M2Crypto"""

import hashlib, os
from base64 import b64encode, b64decode
from M2Crypto import X509, RSA, BIO, m2, EVP
from xbe.xml.security_exceptions import *

class Subject(object):
    def __init__(self, text):
        self.__text = text
        self.__dict__.update(
            dict([c.split("=", 1) for c in text[1:].split("/")])
        )

    def __getitem__(self, x):
        return getattr(self, x)

    def __eq__(self, other):
        return self.__text.__eq__(str(other))

    def __str__(self):
        return self.__text

    def __repr__(self):
        return "<%(cls)s CN=%(name)s>" % {
            "cls": self.__class__.__name__,
            "name": self["CN"]
        }

class X509Certificate(object):
    """This class wraps around the M2Crypto.X509 class."""

    def __init__(self, m2_x509, priv_key=None):
        """Initialize a X.509 certificate using a M2Crypto X509 instance.

        if priv_key is given, too, this class may be used to sign/encrypt data.
        """
        if not isinstance(m2_x509, X509.X509):
            raise CertificateCheckFailed(
                "certificate must be a M2Crypto.X509 instance, you gave me: %s" % (m2_x509))
        self.__x509 = m2_x509
        self.__pub_key = RSA.RSA_pub(m2_x509.get_pubkey().get_rsa().rsa)

        if priv_key and not isinstance(priv_key, RSA.RSA):
            raise KeyCheckFailed("the private key must be a M2Crypto.RSA instance.")
        self.__priv_key = priv_key
        self.__padding = RSA.pkcs1_padding

    def subject(self):
        return Subject(str(self.__x509.get_subject()))

    def issuer(self):
        return self.__x509.get_issuer().as_text()

    def m2_x509(self):
        return self.__x509

    def pub_key(self):
        return self.__pub_key

    def priv_key(self):
        return self.__priv_key

    def is_CA(self):
        """represents this certificate a CA certificate?"""
        return self.__x509.check_ca() != 0

    def validate_certificate(self, other):
        """Validate the 'other' certificate using this one."""

        # this might be confusing, but the m2 implementation works the
        # other way around:
        #     let A be the CA-certificate
        #     let B be the certificate that shall be verified
        #
        # m2:  B.verify(A)
        # my-way: A.verify(B)
        return other.__x509.verify(self.__x509.get_pubkey())

    def is_validated_by(self, ca_cert):
        """can this certificate be validated by the given CA-certificate"""
        return ca_cert.validate_certificate(self)        

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
        return b64encode(self.priv_key().sign(_dgst, algo))

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
        dec_signature = b64decode(signature)
        _dgst = digest(data, algo)
        try:
            self.pub_key().verify(_dgst, dec_signature, algo)
        except RSA.RSAError, ra:
            raise ValidationError("the given data did not match the signature!", ra)
        return True

    def msg_encrypt(self, data, encode=True):
        """return the base64 encoded encryption of 'data'.

        if encode is True (default), return the value in base64 encoding.
        """
        cipher = self.pub_key().public_encrypt(data, self.__padding)
        if encode: cipher = b64encode(cipher)
        return cipher
        
    def msg_decrypt(self, cipher, decode=True):
        """return the decrypted value of the cipher.

        if decode is True (default), asume that cipher is base64
        encoded and decode it first.
        """
        if self.priv_key() is None:
            raise RuntimeError("decryption requires a private key, sorry.")
        if decode: cipher = b64decode(cipher)
        return self.priv_key().private_decrypt(cipher, self.__padding)

    def as_der(self, encode=True):
        """return the x509 certificate as DER encoding."""
        der = self.__x509.as_der()
        if encode:
            return b64encode(der)
        return der

    def as_der_stack(self, encode=True):
        """return the x509 certificate as a X509_Stack in DER encoding."""
        stack = X509.X509_Stack()
        stack.push(self.__x509)
        der = stack.as_der()
        if encode:
            return b64encode(der)
        return der

    def load(cls, crt, key_string=None):
        """load the certificate and probably a RSA key from crt and key_string respectively."""
        x509 = X509.load_cert_string(crt)
        key = key_string and RSA.load_key_string(key_string) or None
        return cls(x509, key)
    load = classmethod(load)

    def load_der(cls, der_crt, decode=True):
        """load a certificate from a string (DER encoded certificate)."""
        # make a PEM
        pem = "\n".join(["-----BEGIN CERTIFICATE-----", der_crt.strip(), "-----END CERTIFICATE-----\n"])
        print pem
        x509 = X509.load_cert_string(pem)
        return cls(x509)
    load_der = classmethod(load_der)

    def load_der_stack(cls, der_crt_stack, decode=True):
        """load a certificate from a string (DER encoded certificate stack)."""
        if decode:
            der_crt_stack = b64decode(der_crt_stack)
        stack = X509.new_stack_from_der(der_crt_stack)
        x509 = stack.pop()
        return cls(x509)
    load_der_stack = classmethod(load_der_stack)

    def load_from_files(cls, crt_path, key_path=None):
        """Loads the certificate from the given files.

        crt_path - points to the file containing the X509 certificate
        key_path - if not None points to the file containing the RSA private key
        """
        x509 = X509.load_cert(crt_path)
        key = key_path and RSA.load_key(key_path)
        return cls(x509, key)
    load_from_files = classmethod(load_from_files)

class Cipher(object):
    """wraps the EVP.Cipher class.

    This class is needed to generate a symetric cipher algorithm. This
    algorithm is then used to encrypt huge amounts of data using a
    randomly generated key. The recipient gets the key encrypted with
    his public-key.
    """

    ALG_DES_EDE3_CBC = "des_ede3_cbc"
    def __init__(self, key=None, IV=None, algorithm=ALG_DES_EDE3_CBC, do_encryption=None, encoding=None):
        """Initialize a new Cipher object, that can be used to encrypt arbitrary data.

        if key is None, asume encryption and generate a random key (128 byte).
        if do_encryption is None and key is None, asume encryption mode
        if do_encryption is None and key is not None, asume decryption
        if do_encryption is True, encrypt data
        if do_encryption is False, decrypt data

        encoding is a python-callable, that gets called on the data
        after/before encryption/decryption the default is base64
        """
        if key is None:
            # generate random key
            key = self.__random_value()
            if do_encryption is None:
                # asume encryption
                do_encryption = True
        elif key is not None and do_encryption is None:
            # asume decryption
            do_encryption = False
        if IV is None:
            if not do_encryption:
                raise ValueError("I need the initial vector for decryption")
            # generate a random initial vector
            IV = self.__random_value()
            
        assert (do_encryption is not None)
        key, IV = map(str, (key, IV))
        if encoding is None:
            encoding = [b64decode, b64encode][do_encryption]
        self.__do_encryption = do_encryption
        self.__encoding = encoding
        self.__key = key
        self.__IV = IV
        self.__algorithm = algorithm
        self.__evp_cipher = EVP.Cipher(algorithm, key, IV, op=int(do_encryption))

    def __random_value(self, nbytes=128):
        if nbytes <= 0:
            raise ValueError("nbytes must be greater than zero: %d" % nbytes)
        try:
            return os.urandom(nbytes)
        except NotImplementedError:
            return str(random.randint(0, int("ff"*nbytes, 16)))

    def key(self):
        return self.__key
    def IV(self):
        return self.__IV
    def algorithm(self):
        return self.__algorithm

    def __call__(self, data, encrypt=None):
        """calls the cipher algorithm with data and returns the result.

        if final_part is True (default), concatenate the result of
        'final' (call to the underlying implementation).
        """
        if self.__do_encryption is False:
            data = self.__encoding(data)
        result = []
        result.append(self.__evp_cipher.update(data))
        result.append(self.__evp_cipher.final())
        if self.__do_encryption:
            return self.__encoding("".join(result))
        else:
            return "".join(result)

__all__ = [ "X509Certificate", "Cipher", "Subject" ]
