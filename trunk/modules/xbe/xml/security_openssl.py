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

"""Security classes using OpenSSL"""

import os, random, tempfile, hashlib, subprocess

import logging
log = logging.getLogger(__name__)

from base64 import b64encode, b64decode
from xbe.xml.security_exceptions import *

class Subject(object):
    def __init__(self, text):
        self.__text = text
        for c in text.split("/"):
            if len(c):
                try:
                    k, v = c.split("=", 1)
                    self.__dict__[k] = v
                except Exception, e:
                    log.warn("invalid subject line `%s': %s", text, str(e))

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
    """This class wraps around the openssl command."""

    def __init__(self, x509, priv_key=None, format="der"):
        """Initialize a X.509 certificate.

        @param x509 a certificate in DER format (string)

        if priv_key is given, too, this class may only be used to sign/encrypt data.
        """
        self.__x509 = x509
        self.__priv_key = priv_key
        self.__format = format

    def format(self):
        return self.__format
    def path(self):
        return self.__path

    def _openssl(self, input=None, *args, **kw):
        argv = ["openssl"]
        argv.extend(args)
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(input)
        return out, err, p.returncode

    def subject(self):
        out, err, exitcode = self._openssl(self.x509(), "x509", "-inform", self.format(), "-subject", "-noout")
        if exitcode == 0:
            subj = out.strip().lstrip("subject= ")
            return Subject(subj)
        else:
            raise RuntimeError("openssl failed (%d): %s" % (exitcode, error))

    def issuer(self):
        out, err, exitcode = self._openssl(self.x509(), "x509", "-inform", self.format(), "-issuer", "-noout")
        if exitcode == 0:
            issuer = out.strip().lstrip("issuer= ")
            return Subject(issuer)
        else:
            raise RuntimeError("openssl failed (%d): %s" % (exitcode, error))

    def x509(self):
        return self.__x509

    def pub_key(self):
        return self.__pub_key

    def priv_key(self):
        return self.__priv_key

    def get_purposes(self):
        output, error, exitcode = self._openssl(self.x509(), "x509", "-noout", "-purpose")
        if exitcode == 0:
            purposes = {}
            for line in output.split("\n"):
                if not len(line): continue
                purpose, yes_no = map(lambda x: x.strip(), line.split(":"))
                yes_no = yes_no.lower()
                if yes_no == "yes":
                    purposes[purpose] = True
                else:
                    purposes[purpose] = False
            return purposes
        else:
            raise RuntimeError("openssl failed (%d): %s" % (exitcode, output))

    def is_CA(self):
        purposes = self.get_purposes()
        return purposes.get("SSL client CA") or purposes.get("SSL server CA")
        
    def validate_certificate(self, other):
        """Validate the 'other' certificate using this one."""

        # this might be confusing, but the m2 implementation works the
        # other way around:
        #     let A be the CA-certificate
        #     let B be the certificate that shall be verified
        #
        # m2:  B.verify(A)
        # my-way: A.verify(B)
        temp = tempfile.NamedTemporaryFile()
        temp.write(self.x509())
        temp.flush()
        try:
            output, error, exitcode = self._openssl(other.x509(), "verify", "-CAfile", temp.name)
            if exitcode == 0 and output.strip().endswith("stdin: OK"):
                return True
            else:
                return False
#                raise CertificateVerificationFailed("certificate is not signed by me")
        finally:
            temp.close()

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
        temp = tempfile.NamedTemporaryFile()
        temp.write(self.priv_key())
        temp.flush()
        try:
            output, error, exitcode = self._openssl(_dgst, "rsautl", "-sign", "-keyform", self.format(), "-inkey", temp.name)
            if exitcode == 0:
                return b64encode(output)
            else:
                raise ValueError("could not sign data, openssl failed (%d): %s: %s" % (exitcode, repr(output), repr(error)))
        finally:
            temp.close()

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

        temp = tempfile.NamedTemporaryFile()
        temp.write(self.x509())
        temp.flush()
        try:
            output, error, exitcode = self._openssl(dec_signature, "rsautl", "-verify", "-keyform", self.format(),
                                                    "-certin", "-inkey", temp.name)
            if exitcode == 0:
                return _dgst == output
            else:
                raise RuntimeError("openssl failed: %d" % exitcode, output, error, exitcode)
        finally:
            temp.close()

    def msg_encrypt(self, data, encode=True):
        """return the base64 encoded encryption of 'data'.

        if encode is True (default), return the value in base64 encoding.
        """
        temp = tempfile.NamedTemporaryFile()
        temp.write(self.x509())
        temp.flush()
        try:
            output, error, exitcode = self._openssl(data, "rsautl", "-encrypt", "-keyform", self.format(), "-certin", "-inkey", temp.name)
            if exitcode == 0:
                if encode:
                    return b64encode(output)
                else:
                    return output
            else:
                raise RuntimeError("openssl failed: %d" % exitcode, output, error, exitcode)
        finally:
            temp.close()
        
    def msg_decrypt(self, cipher, decode=True):
        """return the decrypted value of the cipher.

        if decode is True (default), asume that cipher is base64
        encoded and decode it first.
        """
        if self.priv_key() is None:
            raise RuntimeError("decryption requires a private key, sorry.")
        temp = tempfile.NamedTemporaryFile()
        temp.write(self.priv_key())
        temp.flush()
        try:
            if decode:
                cipher = b64decode(cipher)
            output, error, exitcode = self._openssl(cipher, "rsautl", "-decrypt", "-keyform", self.format(), "-inkey", temp.name)
            if exitcode == 0:
                return output
            else:
                raise RuntimeError("openssl failed: %d" % exitcode, output, error, exitcode)
        finally:
            temp.close()
            
    def as_pem(self):
        output, error, exitcode = self._openssl(self.x509(), "x509", "-inform", self.format(), "-outform", "pem")
        if exitcode == 0:
            return output
        else:
            raise RuntimeError("openssl failed: %d" % exitcode, output, error, exitcode)

    def as_der(self, encode=True):
        """return the x509 certificate as a X509_Stack in DER encoding."""
        if self.format() == "der":
            der = self.x509()
        else:
            output, error, exitcode = self._openssl(self.x509(), "x509", "-outform", "DER", "-inform", self.format())
            if exitcode == 0:
                der = output
            else:
                raise RuntimeError("openssl failed (%d): %s" % (exitcode, output))
        if encode:
            return b64encode(der)
        return der

    def load(cls, crt, key_string=None):
        """load the certificate and probably a RSA key from crt and key_string respectively."""
        return cls(crt, key_string, format="pem")
    load = classmethod(load)

    def load_der(cls, der_crt, decode=True):
        """load a certificate from a string (DER encoded certificate stack)."""
        if decode:
            der_crt = b64decode(der_crt)
        x509 = der_crt
        return cls(x509, format="der")
    load_der = classmethod(load_der)

    def load_from_files(cls, crt_path, key_path=None):
        """Loads the certificate from the given files.

        crt_path - points to the file containing the X509 certificate
        key_path - if not None points to the file containing the RSA private key
        """
        x509 = open(crt_path).read()
        key = key_path and open(key_path).read() or None
        return cls(x509, key, format="pem")
    load_from_files = classmethod(load_from_files)

class Cipher(object):
    """wraps openssl enc

    This class is needed to generate a symetric cipher algorithm. This
    algorithm is then used to encrypt huge amounts of data using a
    randomly generated key. The recipient gets the key encrypted with
    his public-key.
    """

    ALG_DES_EDE3_CBC = "des_ede3_cbc"
    ALG_AES_256_CBC = "aes_256_cbc"
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
            key = hex(self.__random_value(16))[2:].rstrip("L")
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
            IV = hex(self.__random_value(16))[2:].rstrip("L")
            
        assert (do_encryption is not None)

        self.__do_encryption = do_encryption
        self.__key = key
        self.__IV  = IV
        self.__algorithm = algorithm

    def __random_value(self, nbytes=16):
        if nbytes <= 0:
            raise ValueError("nbytes must be greater than zero: %d" % nbytes)
        return int(random.randint(0, int("ff"*nbytes, 16)))
#        try:
#            return os.urandom(nbytes)
#        except NotImplementedError:

    def key(self):
        return str(self.__key)
    def IV(self):
        return str(self.__IV)
    def algorithm(self):
        return self.__algorithm

    def _openssl(self, input=None, *args, **kw):
        argv = ["openssl"]
        argv.extend(args)
        p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate(input)
        return out, err, p.returncode

    def __call__(self, data, encrypt=None):
        """calls the cipher algorithm with data and returns the result."""
        if encrypt is None:
            encrypt = self.__do_encryption
        enc_dec_flag = ["-d", "-e"][encrypt]
        algo = "-%s" % self.algorithm().replace("_", "-")
        if not encrypt:
            data = b64decode(data)
        output, error, exitcode = self._openssl(data, "enc", enc_dec_flag, algo,
                                                "-K", self.key(), "-iv", self.IV())
        if encrypt:
            output = b64encode(output)
        if exitcode == 0:
            return output
        else:
            raise RuntimeError("openssl failed (%d): %s" % (exitcode, error))

__all__ = ["X509Certificate", "Cipher", "Subject"]
