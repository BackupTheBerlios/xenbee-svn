#!/usr/bin/env python
"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging
log = logging.getLogger(__name__)

import base64, hashlib
from M2Crypto import X509, RSA, BIO, m2
from lxml import etree
from xbe.xml import cloneDocument
from xbe.xml.namespaces import XBE, DSIG, XBE_SEC
from zope.interface import Interface, implements

class SecurityError(Exception):
    pass

class ValidationError(SecurityError):
    pass

class CertificateCheckFailed(ValueError):
    pass

class CertificateVerificationFailed(ValidationError):
    pass

class PrivateKeyCheckFailed(ValueError):
    pass


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
        
    def subject(self):
        return self.__x509.get_subject()

    def issuer(self):
        return self.__x509.get_issuer()

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

    def sign_encrypt(msg):
        """encrypts the message and adds a signature to the given message.

        returns the signed + encrypted."""

    def validate_decrypt(msg):
        """validates and decrypts the given msg.

        returns the validated and decrypted message.
        raises ValidationError on error
        """

class NullSecurityLayer:
    """The simplest of all security methods: no security at all.

    each method simply returns its argument.
    """
    implements(ISecurityLayer)
    
    def sign_encrypt(self, msg):
        return msg

    def validate_decrypt(self, msg):
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
    SecurityPipe may refer to them uniformly.

    And of course the CA-certificate for validation.
    """
    implements(ISecurityLayer)
    def __init__(self, my_cert, other_cert, ca_certs):
        if not isinstance(my_cert, X509Certificate):
            raise CertificateCheckFailed("X509Certificate required, you gave me: %s" % (my_cert))
        self.__my_cert = my_cert
        if not isinstance(other_cert, X509Certificate):
            raise CertificateCheckFailed("X509Certificate required, you gave me: %s" % (other_cert))
        self.__other_cert = other_cert
        self.__ca_certs = ca_certs


    def sign_encrypt(self, _msg):
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
           <xbe:MessageHeader>
              <xbe-sec:SecurityInformation>
                  <dsig:Signature>
                     <dsig:KeyInfo>
                        <dsig:X509Certificate>
                         <!-- base64 DER encoding of 'my_cert' -->
                        </dsig:X509Certificate>
                     </dsig:KeyInfo>
                     <dsig:SignatureValue>
                        <!-- base64 encoded signature of the whole message -->
                     </dsig:SignatureValue>
                  </dsig:Signature>
              </xbe-sec:SecurityInformation>
           </xbe:MessageHeader>
           <xbe:MessageBody>
              <xbe-sec:CipherData>
                 <xbe-sec:CipherValue>
                    <!-- base64 encoded encryption of real body -->
                 </xbe-sec:CipherValue>
              </xbe-sec:CipherData>
           </xbe:MessageBody>
        </xbe:Message>
        """
        msg = cloneDocument(_msg)
        hdr = msg.find(XBE("MessageHeader"))
        if hdr is None:
            raise ValueError("the message requires a header: '%s'" % (etree.tostring(hdr)))
        bod = msg.find(XBE("MessageBody"))
        if bod and len(bod) > 1:
            raise ValueError("only one child element allowed in body.")

        nsmap = { "xbe": str(XBE),
                  "xbe-sec": str(XBE_SEC),
                  "dsig": str(DSIG) }
        
        # append securityInformation
        sec_info = etree.SubElement(hdr, XBE_SEC("SecurityInformation"), nsmap=nsmap)
        dsig_sig = etree.SubElement(sec_info, DSIG("Signature"), nsmap=nsmap)
        dsig_key = etree.SubElement(dsig_sig, DSIG("KeyInfo"))
        etree.SubElement(dsig_key, DSIG("X509Certificate")).text = self.__my_cert.as_der()

        # sign the whole message as it is right now and put it into the header
        signature = self.__my_cert.msg_signature(etree.tostring(msg))
        etree.SubElement(dsig_sig, DSIG("SignatureValue")).text = signature
        
        if bod is None or len(bod) == 0:
            # empty body may be ignored
            return msg
        # encrypt the element
        element = bod[0]
        cipher = self.__other_cert.msg_encrypt(etree.tostring(element))

        # remove it from the tree and replace it by the CipherData
        bod.remove(element)
        cipher_data = etree.SubElement(bod, XBE_SEC("CipherData"), nsmap=nsmap)
        etree.SubElement(cipher_data, XBE_SEC("CipherValue")).text = cipher
        
        return msg

    def validate_decrypt(self, _msg):
        msg = cloneDocument(_msg)
        # decrypt the body, if there is one
        bod = msg.find(XBE("MessageBody"))
        if bod and len(bod) != 0:
            cipher_data = bod.find(XBE_SEC("CipherData"))
            if cipher_data is None:
                raise SecurityError("could not find CipherData!")
            bod.remove(cipher_data)
            
            cipher_value = cipher_data.find(XBE_SEC("CipherValue"))
            cipher = cipher_value.text
            cleartext = self.__my_cert.msg_decrypt(cipher)

            # parse as xml
            real_body = etree.fromstring(cleartext)
            bod.append(real_body)

        # validate everything
        hdr = msg.find(XBE("MessageHeader"))
        sec_info = hdr.find(XBE_SEC("SecurityInformation"))
        dsig = sec_info.find(DSIG("Signature"))
        cert_text = dsig.find(DSIG("KeyInfo/X509Certificate")).text
        x509 = X509Certificate.load_der(cert_text)

        signature_value = dsig.find(DSIG("SignatureValue"))
        dsig.remove(signature_value)

        # validate the x509 certificate
        if len(self.__ca_certs):
            ca = self.__ca_certs[0]
            if not ca.validate_certificate(x509):
                raise ValidationError("X.509 certificate could not be validated")

        # validate the signature
        x509.msg_validate(etree.tostring(msg), signature_value.text)
        return msg

__all__ = [
    "ValidationError", "CertificateCheckFailed", "CertificateVerificationFailed",
    "PrivateKeyCheckFailed", "X509Certificate", "CertificateStore", "ISecurityLayer",
    "NullSecurityLayer", "X509SecurityLayer" ]
    
