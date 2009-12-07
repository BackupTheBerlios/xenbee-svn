# XenBEE is a software that provides execution of applications
# in self-contained virtual disk images on a remote host featuring
# the Xen hypervisor.
#
# Copyright (C) 2007 Alexander Petry <petry@itwm.fhg.de>.
# This file is part of XenBEE.

# XenBEE is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# XenBEE is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""
The Xen Based Execution Environment XML Messages
"""

__version__ = "$Rev$"
__author__ = "$Author$"

import logging, random, os
log = logging.getLogger(__name__)

import hashlib
from base64 import b64encode, b64decode
from pprint import pformat
from lxml import etree
from xbe.xml.security_exceptions import *
from xbe.xml import cloneDocument
from xbe.xml.namespaces import XBE, DSIG, XBE_SEC
from zope.interface import Interface, implements

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

use_m2 = False
if use_m2:
    from xbe.xml.security_m2 import *
else:
    from xbe.xml.security_openssl import *

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
            etree.SubElement(dsig_key, DSIG("X509Certificate")).text = self.__my_cert.as_pem()

        # sign the whole message as it is right now and put it into the header
        c14n = StringIO()
        _msg.getroottree().write_c14n(c14n)
        signature = self.__my_cert.msg_signature(c14n.getvalue())
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
                if self.__other_cert.as_pem() != cert_text:
                    raise SecurityError("the included certificate does not match the saved certificate.")
            else:
                valid = False
                # validate the x509 certificate
                cert = X509Certificate.load(cert_text)
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
        c14n = StringIO()
        _msg.getroottree().write_c14n(c14n)

        x509.msg_validate(c14n.getvalue(), signature_value.text)
        return _msg

    def encrypt(self, msg):
        """Encrypts the given messgage.

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
            <xbe-sec:CipherInfo>
              <!-- the following key is encrypted using the public key -->
              <xbe-sec:CipherKey>base64 encoded encrypted symetric key</xbe-sec:CipherKey>
              <xbe-sec:CipherIV>base64 encoded initial vector</xbe-sec:CipherIV>
              <xbe-sec:CipherAlgorithm>the algorithm used to encrypt/decrypt data</xbe-sec:CipherAlgorithm>
            </xbe-sec:CipherInfo>
          </xbe:MessageHeader>
          <xbe:MessageBody>
            <xbe-sec:CipherData>
              <xbe-sec:CipherValue>
                <!-- base64 encoded encryption of real body using CipherKey -->
              </xbe-sec:CipherValue>
            </xbe-sec:CipherData>
           </xbe:MessageBody>
        </xbe:Message>
        """

        def _wrap_it(text):
            from textwrap import wrap
            return "\n"+"\n".join(wrap(text))+"\n"
        
        # generate a Cipher algorithm
        cipher = Cipher(do_encryption=True)
        
        # encrypt the whole message
        enc_message = _wrap_it(cipher(etree.tostring(msg, xml_declaration=True)))
        # encrypt the key using the public key of our recipient
        enc_key = _wrap_it(self.__other_cert.msg_encrypt(cipher.key()))
        enc_iv  = _wrap_it(self.__other_cert.msg_encrypt(cipher.IV()))

        nsmap = { "xbe": str(XBE),
                  "xbe-sec": str(XBE_SEC) }

        # create a new message and append necessary information
        _msg = etree.Element(XBE("Message"), nsmap=nsmap)
        
        hdr = etree.SubElement(_msg, XBE("MessageHeader"))
        cipher_info = etree.SubElement(hdr, XBE_SEC("CipherInfo"))
        etree.SubElement(cipher_info, XBE_SEC("CipherKey")).text = enc_key
        etree.SubElement(cipher_info, XBE_SEC("CipherIV")).text = enc_iv
        etree.SubElement(cipher_info, XBE_SEC("CipherAlgorithm")).text = cipher.algorithm()

        bod = etree.SubElement(_msg, XBE("MessageBody"))
        cipher_data = etree.SubElement(bod, XBE_SEC("CipherData"))
        etree.SubElement(cipher_data, XBE_SEC("CipherValue")).text = enc_message
        return _msg

    def decrypt(self, msg):
        cipher_info = msg.find(XBE("MessageHeader")+"/"+XBE_SEC("CipherInfo"))
        if cipher_info is None:
            raise SecurityError("could not find CipherInfo")
        enc_key = cipher_info.findtext(XBE_SEC("CipherKey"))
        if enc_key is None:
            raise SecurityError("could not find CipherKey")
        enc_iv = cipher_info.findtext(XBE_SEC("CipherIV"))
        if enc_iv is None:
            raise SecurityError("could not find CipherIV")
        enc_alg = cipher_info.findtext(XBE_SEC("CipherAlgorithm"))
        if enc_alg is None:
            raise SecurityError("could not find CipherAlgorithm")
        
        cipher_data = msg.find(XBE("MessageBody")+"/"+XBE_SEC("CipherData"))
        if cipher_data is None:
            raise SecurityError("could not find CipherData")
        key = self.__my_cert.msg_decrypt(enc_key)
        IV = self.__my_cert.msg_decrypt(enc_iv)
        # create Cipher algorithm
        decipher = Cipher(key=key, IV=IV, algorithm=enc_alg, do_encryption=False)

        cipher_value = cipher_data.findtext(XBE_SEC("CipherValue"))
        real_msg = decipher(cipher_value)
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
    
