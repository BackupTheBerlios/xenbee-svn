#!/usr/bin/env python
"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, random, os
log = logging.getLogger(__name__)

import base64, hashlib
from M2Crypto import X509, RSA, BIO, m2, EVP
from pprint import pformat
from lxml import etree
from xbe.xml import cloneDocument
from xbe.xml.namespaces import XBE, DSIG, XBE_SEC
from zope.interface import Interface, implements

class SecurityError(Exception):
    pass

class ValidationError(SecurityError):
    pass

class SignatureMissing(ValidationError):
    pass

class CertificateMissing(SecurityError):
    pass

class CertificateCheckFailed(ValueError):
    pass

class CertificateVerificationFailed(ValidationError):
    pass

class PrivateKeyCheckFailed(ValueError):
    pass


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

    def __init__(self, m2_x509, priv_key=None, padding=RSA.pkcs1_padding):
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
        self.__padding = padding

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
        cipher = self.pub_key().public_encrypt(data, self.__padding)
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
        return self.priv_key().private_decrypt(cipher, self.__padding)

    def as_der(self, encode=True):
        """return the x509 certificate as a X509_Stack in DER encoding."""
        stack = X509.X509_Stack()
        stack.push(self.__x509)
        der = stack.as_der()
        if encode:
            return base64.b64encode(der)
        return der

    def load(cls, crt, key_string=None):
        """load the certificate and probably a RSA key from crt and key_string respectively."""
        x509 = X509.load_cert_string(crt)
        key = key_string and RSA.load_key_string(key_string)
        return cls(x509, key)
    load = classmethod(load)

    def load_der(cls, der_crt_stack, decode=True):
        """load a certificate from a string (DER encoded certificate stack)."""
        if decode:
            der_crt_stack = base64.b64decode(der_crt_stack)
        stack = X509.new_stack_from_der(der_crt_stack)
        x509 = stack.pop()
        return cls(x509)
    load_der = classmethod(load_der)

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
            if encoding is None:
                encoding = base64.b64encode
        elif key is not None and do_encryption is None:
            # asume decryption
            do_encryption = False
            if encoding is None:
                encoding = base64.b64decode
        if IV is None:
            if not do_encryption:
                raise ValueError("I need the initial vector for decryption")
            # generate a random initial vector
            IV = self.__random_value()
            
        assert (do_encryption is not None)

        if encoding is None:
            encoding = [base64.b64decode, base64.b64encode][do_encryption]
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

    def __call__(self, data, final_part=True):
        """calls the cipher algorithm with data and returns the result.

        if final_part is True (default), concatenate the result of
        'final' (call to the underlying implementation).
        """
        result = []
        result.append(self.__evp_cipher.update(data))
        if final_part:
            result.append(self.__evp_cipher.final())
        return "".join(result)

class CertificateStore(object):
    instance = None

    def __init__(self):
        self.__certs = {}   # holds a mapping from 'subject-DN' to cert
        self.__cas = []     # holds all valid CA certificates

    def register_ca(self, ca_cert):
        """Register a new CA-certificate with this store."""
        if not isinstance(ca_cert, X509Certificate):
            # try to wrap it (raises CertificateCheckFailed)
            ca_cert = X509Certificate(ca_cert)
        self.__cas.append(ca_cert)

    def register_certificate(self, cert, key=None):
        """Register a new certificate with this store.

        if key is None (default), the subject-DN is used.
        """
        if not isinstance(cert, X509Certificate):
            # try to wrap it (raises CertificateCheckFailed)
            cert = X509Certificate(cert)
        self.verify(cert)

        # read the key
        key = key or cert.subject()
        self.__certs[key] = cert

    def to_der(self):
        """return a DER representation (DER encoded certificate stack)."""
        pass

    def lookup_cert(self, key):
        """lookup a certificate by some key"""
        return self.__certs[key]


class ISecurityLayer(Interface):
    """The security pipeline interface.

    encrypt(msg)
    decrypt(msg)
    """

    def sign(msg, include_certificate):
        """signs the given message."""

    def validate(msg):
        """validates the message using the signature within the message."""

    def encrypt(msg):
        """encrypt the given message."""

    def decrypt(msg):
        """decrypt the given message."""

    def sign_and_encrypt(msg, include_certificate):
        """encrypts the message and adds a signature to the given message.

        returns the signed + encrypted."""

    def validate_and_decrypt(msg):
        """validates and decrypts the given msg.

        returns the validated and decrypted message.
        raises ValidationError on error
        """

class NullSecurityLayer:
    """The simplest of all security methods: no security at all.

    each method simply returns its argument.
    """
    implements(ISecurityLayer)
    
    def sign_and_encrypt(self, msg, include_certificate):
        return msg

    def validate_and_decrypt(self, msg):
        return msg

    def sign(self, msg, include_certificate):
        return msg

    def validate(self, msg):
        return msg

class X509SecurityLayer:
    """I represent a pipeline, that can be used to encrypt/sign
    messages for sending purposes and decrypt on receiving.

    Holds needed keys and certificates for the desired operations.

    For encryption it must hold:
         * sender certificate + private key (for signing)
         * receiver certificate

    For decryption it must hold:
         * sender certificate (for validation)
         * receiver certificate + private key (for decryption)

    The information is kept in generic placeholders, so that the
    SecurityLayer may refer to them uniformly.

    And of course the CA-certificate for validation.
    """
    implements(ISecurityLayer)
    def __init__(self, my_cert, other_cert, ca_certs):
        if not isinstance(my_cert, X509Certificate):
            raise CertificateCheckFailed("X509Certificate required, you gave me: %s" % (my_cert))
        self.__my_cert = my_cert
        if other_cert and not isinstance(other_cert, X509Certificate):
            raise CertificateCheckFailed("X509Certificate required, you gave me: %s" % (other_cert))
        self.__other_cert = other_cert
        self.__ca_certs = ca_certs

    def other_cert(self):
        return self.__other_cert

    def sign(self, msg, include_certificate=False):
        _msg = cloneDocument(msg)
        hdr = _msg.find(XBE("MessageHeader"))
        if hdr is None:
            raise ValueError("the message requires a header!")
        nsmap = { "xbe": str(XBE),
                  "xbe-sec": str(XBE_SEC),
                  "dsig": str(DSIG) }
        # append securityInformation
        sec_info = etree.SubElement(hdr, XBE_SEC("SecurityInformation"), nsmap=nsmap)
        dsig_sig = etree.SubElement(sec_info, DSIG("Signature"), nsmap=nsmap)
        if include_certificate:
            dsig_key = etree.SubElement(dsig_sig, DSIG("KeyInfo"))
            etree.SubElement(dsig_key, DSIG("X509Certificate")).text = self.__my_cert.as_der()

        # sign the whole message as it is right now and put it into the header
        signature = self.__my_cert.msg_signature(etree.tostring(_msg))
        etree.SubElement(dsig_sig, DSIG("SignatureValue")).text = signature
        
        return (_msg, signature)

    def validate(self, msg):
        if isinstance(msg, tuple):
            msg = msg[0]
        _msg = cloneDocument(msg)
        
        # validate everything
        dsig = _msg.find(XBE("MessageHeader") + "/" +
                         XBE_SEC("SecurityInformation") + "/" +
                         DSIG("Signature"))
        if dsig is None:
            raise SignatureMissing("No signature found")
        
        cert_text = dsig.findtext(DSIG("KeyInfo/X509Certificate"))
        if cert_text:
            if self.__other_cert:
                # check if they are the same, else raise an error
                if self.__other_cert.as_der() != cert_text:
                    raise SecurityError("the included certificate does not match the saved certificate.")
            else:
                valid = False
                # validate the x509 certificate
                cert = X509Certificate.load_der(cert_text)
                for ca in self.__ca_certs:
                    if ca.validate_certificate(cert):
                        valid = True; break
                if not valid:
                    raise ValidationError("X.509 certificate could not be validated")
                self.__other_cert = cert

        x509 = self.__other_cert
        if x509 is None:
            raise CertificateMissing(
                "cannot verify message, since i do not have the matching certificate")

        signature_value = dsig.find(DSIG("SignatureValue"))
        dsig.remove(signature_value)

        # validate the signature
        x509.msg_validate(etree.tostring(_msg), signature_value.text)
        return _msg

    def encrypt(self, msg):
        """Signs and encrypts the given messgage.

        my_cert needs to hold a X509 certificate *and* a private key.
        other_cert must hold a X509 certificate.


        The following message structure is assumed:

        <xbe:Message>
           <xbe:MessageHeader>
           </xbe:MessageHeader>
           <xbe:MessageBody>
              <xsd:any/>?
           </xbe:MessageBody>
        </xbe:Message>

        The result will look like:
        
        <xbe:Message>
          <xbe-sec:CipherData>
            <!-- the following key is encrypted using the public key -->
            <xbe-sec:CipherKey>base64 encoded encrypted symetric key</xbe-sec:CipherKey>
            <xbe-sec:CipherIV>base64 encoded initial vector</xbe-sec:CipherIV>
            <xbe-sec:CipherAlgorithm>the algorithm used to encrypt/decrypt data</xbe-sec:CipherAlgorithm>
            <xbe-sec:CipherValue>
              <!-- base64 encoded encryption of real body using CipherKey -->
            </xbe-sec:CipherValue>
          </xbe-sec:CipherData>
        </xbe:Message>
        """

        def _wrap_it(text):
            from textwrap import wrap
            return "\n"+"\n".join(wrap(text))+"\n"
        
        # generate a Cipher algorithm
        cipher = Cipher(do_encryption=True, algorithm=Cipher.ALG_DES_EDE3_CBC)
        
        # encrypt the whole message
        enc_message = _wrap_it(base64.b64encode(cipher(etree.tostring(msg, xml_declaration=True))))
        # encrypt the key using the public key of our recipient
        enc_key = _wrap_it(self.__other_cert.msg_encrypt(cipher.key()))
        enc_iv  = _wrap_it(self.__other_cert.msg_encrypt(cipher.IV()))
        del cipher

        nsmap = { "xbe": str(XBE),
                  "xbe-sec": str(XBE_SEC) }

        # create a new message and append necessary information
        _msg = etree.Element(XBE("Message"), nsmap=nsmap)
        etree.SubElement(_msg, XBE("MessageHeader"))
        bod = etree.SubElement(_msg, XBE("MessageBody"))
        cipher_data = etree.SubElement(bod, XBE_SEC("CipherData"))
        etree.SubElement(cipher_data, XBE_SEC("CipherKey")).text = enc_key
        etree.SubElement(cipher_data, XBE_SEC("CipherIV")).text = enc_iv
        etree.SubElement(cipher_data, XBE_SEC("CipherAlgorithm")).text = Cipher.ALG_DES_EDE3_CBC
        etree.SubElement(cipher_data, XBE_SEC("CipherValue")).text = enc_message
        return _msg

    def decrypt(self, msg):
        cipher_data = msg.find(XBE("MessageBody")+"/"+XBE_SEC("CipherData"))
        if cipher_data is None:
            raise SecurityError("could not find CipherData")
        enc_key = cipher_data.findtext(XBE_SEC("CipherKey"))
        if enc_key is None:
            raise SecurityError("could not find CipherKey")
        enc_iv = cipher_data.findtext(XBE_SEC("CipherIV"))
        if enc_iv is None:
            raise SecurityError("could not find CipherIV")
        enc_alg = cipher_data.findtext(XBE_SEC("CipherAlgorithm"))
        if enc_alg is None:
            raise SecurityError("could not find CipherAlgorithm")
        key = self.__my_cert.msg_decrypt(enc_key)
        IV = self.__my_cert.msg_decrypt(enc_iv)
        # create Cipher algorithm
        decipher = Cipher(key=key, IV=IV, algorithm=enc_alg, do_encryption=False)

        cipher_value = cipher_data.findtext(XBE_SEC("CipherValue"))
        real_msg = decipher(base64.b64decode(cipher_value))
        return etree.fromstring(real_msg)

    def sign_and_encrypt(self, msg, include_certificate=False):
        return self.encrypt(self.sign(msg, include_certificate)[0])

    def validate_and_decrypt(self, msg):
        return self.validate(self.decrypt(msg))

    def fully_established(self):
        return self.__my_cert and self.__other_cert

#__all__ = [
#    "ValidationError", "CertificateCheckFailed", "CertificateVerificationFailed",
#    "PrivateKeyCheckFailed", "X509Certificate", "CertificateStore", "ISecurityLayer",
#    "NullSecurityLayer", "X509SecurityLayer", "Cipher" ]
    
