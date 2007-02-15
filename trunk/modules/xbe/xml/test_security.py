#!/usr/bin/python

"""Test for the Security module."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys
from xbe.xml.security import X509Certificate


class TestCertificate(unittest.TestCase):
    __cert = """\
-----BEGIN CERTIFICATE-----
MIIE4jCCA8qgAwIBAgIBAjANBgkqhkiG9w0BAQUFADCBlDEWMBQGA1UEAxMNWEJF
IFNlcnZlciBDQTELMAkGA1UEBhMCREUxGDAWBgNVBAgTD1JoZWlubGFuZC1QZmFs
ejEXMBUGA1UEBxMOS2Fpc2Vyc2xhdXRlcm4xGDAWBgNVBAoTD0ZyYXVuaG9mZXIg
SVRXTTEgMB4GCSqGSIb3DQEJARYRcGV0cnlAaXR3bS5maGcuZGUwHhcNMDcwMjE1
MjAzNTUyWhcNMDgwMjE1MjAzNTUyWjCBizELMAkGA1UEBhMCREUxGDAWBgNVBAgT
D1JoZWlubGFuZC1QZmFsejEYMBYGA1UEChMPRnJhdW5ob2ZlciBJVFdNMRAwDgYD
VQQLEwdQZXJzb25zMRQwEgYDVQQDEwt0ZXN0IHVzZXIgMTEgMB4GCSqGSIb3DQEJ
ARYRcGV0cnlAaXR3bS5maGcuZGUwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEK
AoIBAQDEKm7IrxkK5lmEmgHbpcnD2U8wS9pgTqpkdbEbBEkVlQ9pQM6UxOqmnch8
aNTJJs8rGwh372yf/q9AibBSjl+reOpbH3yct2ECPSfKkdxEHFZQz1peEBK+F1+U
dQdSmYSeanp2fP70Kjix24I4e8StFEwEVXpmXG496RzVba5cKMrdBf+gMg8HOrA+
yeFDD8IaO8vxQMqEsq3eVFrH/ypQL7oPfYwNtHjpZ8co6xwgCnL+28Kwq+KUlXlt
FKJ8Fd/yZqe1dcKrhNV8kttFYK6jC+u07AimKyw5ifYTg1vl7+58hyajZBRr2M3x
VVBfnmdA+2iD4wuN6RxBL6sRGPQHAgMBAAGjggFEMIIBQDAJBgNVHRMEAjAAMB0G
A1UdDgQWBBR3hMTUrXaDZJ6WLEDlGsdHbtZ/mzCByQYDVR0jBIHBMIG+gBSmZgxm
uuS7sXNkjyvwyMuJHI1gv6GBmqSBlzCBlDEWMBQGA1UEAxMNWEJFIFNlcnZlciBD
QTELMAkGA1UEBhMCREUxGDAWBgNVBAgTD1JoZWlubGFuZC1QZmFsejEXMBUGA1UE
BxMOS2Fpc2Vyc2xhdXRlcm4xGDAWBgNVBAoTD0ZyYXVuaG9mZXIgSVRXTTEgMB4G
CSqGSIb3DQEJARYRcGV0cnlAaXR3bS5maGcuZGWCCQDdOSWHDLX9szBIBglghkgB
hvhCAQQEOxY5aHR0cDovL3hlbi1vLW1hdGljLml0d20uZmhyZy5mcmF1bmhvZmVy
LmRlL3hiZS9jYS1jcmwucGVtMA0GCSqGSIb3DQEBBQUAA4IBAQAVxaOnusy1ku7G
I/JBG3u2xPXaIwT++axcYFI+Dz/TmjQlVp64KHIPzVf4syL7yljiWWiQdy6YnbiN
XurN/5dfA3mjTbi2lGoXhqalgtVFCLVcS7YDxPYykb39gurnLUfZXci/pMyZ9Fnr
lXXk4zn93vFIjWvJlqkmOntjXgf0f/hajNwD7Mlo+6tWDdmj4kO7yzo384PVV++N
RZybIT9dpvOHQwfcFxsGRi8wOogmFl59TyRaB9j3tWJn2oxdBf8AMTWWFMvQH23V
Hnz9sZ44fBi2G/aNWwl6ZAJbOynCyyNHk41dD10i+PMApjNwqy4L7X0sOGN9WNTZ
9sEYp1OU
-----END CERTIFICATE-----
"""
    __priv_key = """\
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAxCpuyK8ZCuZZhJoB26XJw9lPMEvaYE6qZHWxGwRJFZUPaUDO
lMTqpp3IfGjUySbPKxsId+9sn/6vQImwUo5fq3jqWx98nLdhAj0nypHcRBxWUM9a
XhASvhdflHUHUpmEnmp6dnz+9Co4sduCOHvErRRMBFV6ZlxuPekc1W2uXCjK3QX/
oDIPBzqwPsnhQw/CGjvL8UDKhLKt3lRax/8qUC+6D32MDbR46WfHKOscIApy/tvC
sKvilJV5bRSifBXf8mantXXCq4TVfJLbRWCuowvrtOwIpissOYn2E4Nb5e/ufIcm
o2QUa9jN8VVQX55nQPtog+MLjekcQS+rERj0BwIDAQABAoIBAQCXfTluq6IIQ9mv
yItUx9Rn9cLsxjdPlpCJ4kWyWn3iN+nd25ltVCDuKP1x7jcdXGYyoL7KeFCHwlQu
3+YV6zNApbE+S7OdBxTYeMfo7PmQc93IrEjaSUlgGYbLjBDqnfnHqO0H4gG2J4D/
AUiwPAynqPwHgMd0kz7jesm0nO5A5jhvuFSLHfdGXY3MO4L3N2RteCKFnxypLrmB
pgQQqlNUtKr8dZrVR+mvbP5v2zoMjFeVx32hTRJ31ak0ieyN4rtNyJMwoRZyVqf9
pGuGNTs87M7E9uiiKli3OVOWLkkQvWqR3Z1DiNr3o5NJKQpFW58qcX73ZJ5fj8mJ
GkHmkPXRAoGBAPNaUDfQ2cGBTt62VQl4N679iY/LTzkrljMkhEEt2N2QlwCTe2UW
wmq6ss0qYujN6MwOBsqq/nespv7Czuw1qpPrqjZU9UOhCpTm0jWjBA6Y5S33mIvc
cJU32qAI/KZktUy8ndkayw43kTCpY67h6gjdgHbQiXcO+BJkxW8IsH3JAoGBAM5c
UdG6Drgof03o8Jcs5S1azD6ERUTtb4VxNxItp4/UeMNu55r4Pyw3XPWuLemLEH/G
SsrO3k5g1jhKYjG3UQN/2E2zVVwRAyAN4zLbDiPZpzc1QzEnDCioyC7RPixfQsdt
OrA/mjhx2GPm+1ciNmwV+a9jZvxGGMkH3vUOpotPAoGAJ3TjQMmKJQfUQ+QIUaq+
TI8rOLdcNwbMKaqoDvFiEjqZYSyIe1F/YFK5Hu7abqjEMCGuFDo5XCoQQYpQhpgE
+krhpEGOKtL3pkDuoGe4Bq3fqt5US4kIcAlIV15dqJT3mGOUrFjdx4ZW8i7kzLww
eBOB+sHBKB6zNjhEksYz55ECgYA8cMe6EK+c+qeGrzJAZPLe3Ngze1Q6gvyF7gn+
Ngb81nNkckg9mHYQQkrk3lYuL//uHKrtSbfM5wn3RLoL67A7wSceYuceZxEuQ0MH
MyeqEmaqgdwjOleSVRUEuV5naqNJe9GTq51E6PtDD3UQKUIdWDZgS1Hvk6xQvRBt
YBQhewKBgQDvHD8nSikMT7hyVmbqBfRvpA2OdejP0MzpYpG0TXG2Klbt47Ou04PK
vttQxyHNFn1QQHXGDl3hhiIbb8YKMcLCxLR0uh04R/NJ3HVD+U4X2MnBuXGPhAOH
pcjKM1iwVaHkpSBfSTleva8hr0lLQihumxlAKOR3JIBvma7DYJpdHg==
-----END RSA PRIVATE KEY-----
"""

    def setUp(self):
	self.data = "The quick brown fox jumps over the lazy dog"
	self.data_sig = """NKfK302gpJwtXe5nnUs3dVjUktnrcVPiJn7xH/LMGjGFTZ+2+482NkxoTHikdrvemBagunBwxKBXTrmntcpUz/kPVNAHdO9Ola/YImIRZntiS3GQ4/OGODaQ4jlnPQPsolNwRdZVzBFY8pbFl0KoQqgcK2367mVWF2FEZmArZRlx3C1Yhqy9AUWfbF78ERFfRE7D5jIIz1FJlZVMw2L7h53Awu1Rw1agvkgR0yvLhWe7rcFNQUFziqJuDEzk7KFq+oH38Hx+VPqWXoLI3JFS1N+d6aaMJKOR6ynjRGUXb+iWlUAdAmLhT8vktcqu/mrhh8omqpqK2NTldJ9NoV5bKA=="""

    def __get_sample_cert(self):
	return X509Certificate.load(TestCertificate.__cert,
				    TestCertificate.__priv_key)

    def test_load(self):
	"""Tests whether loading from file works."""
	try:
	    self.__get_sample_cert()
	except Exception:
	    self.fail("sample certificate could not be built.")

    def test_signing(self):
	"""Tests whether siging as such works."""
	cert = self.__get_sample_cert()
	sig = cert.msg_signature(self.data)
	self.assertEqual(self.data_sig, sig)

    def test_validate(self):
	cert = self.__get_sample_cert()
	try:
	    cert.msg_validate(self.data, self.data_sig)
	except Exception:
	    self.fail("validation failed")

    def test_both(self):
	cert = self.__get_sample_cert()

	test_data = "hello world!"
	sig = cert.msg_signature(test_data)
	try:
	    cert.msg_validate(test_data, sig)
	except Exception:
	    self.fail("validation failed")



def suite():
    s1 = unittest.makeSuite(TestCertificate, 'test')
    return unittest.TestSuite((s1,))

if __name__ == '__main__':
    unittest.main()
