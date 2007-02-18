#!/usr/bin/python

"""Test for the Security module."""

__version__ = "$Rev$"
__author__ = "$Author$"

import unittest, os, sys, base64
from xbe.xml.security import *
from lxml import etree
from xbe.xml.namespaces import XBE

class ExampleData(object):
#########################################################
#                                                       #
#               Required Certificates                   #
#           and keys used for test cases.               #
#                                                       #
#########################################################

    def get_sample_cert(cls):
	return X509Certificate.load(ExampleData.cert,
				    ExampleData.priv_key)
    get_sample_cert = classmethod(get_sample_cert)

    text = """The quick brown fox jumps over the lazy dog"""
    text_sig = """NKfK302gpJwtXe5nnUs3dVjUktnrcVPiJn7xH/LMGjGFTZ+2+482NkxoTHikdrvemBagunBwxKBXTrmntcpUz/kPVNAHdO9Ola/YImIRZntiS3GQ4/OGODaQ4jlnPQPsolNwRdZVzBFY8pbFl0KoQqgcK2367mVWF2FEZmArZRlx3C1Yhqy9AUWfbF78ERFfRE7D5jIIz1FJlZVMw2L7h53Awu1Rw1agvkgR0yvLhWe7rcFNQUFziqJuDEzk7KFq+oH38Hx+VPqWXoLI3JFS1N+d6aaMJKOR6ynjRGUXb+iWlUAdAmLhT8vktcqu/mrhh8omqpqK2NTldJ9NoV5bKA=="""
    

    cert = """\
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

    ca_cert = """
-----BEGIN CERTIFICATE-----
MIIEqjCCA5KgAwIBAgIJAN05JYcMtf2zMA0GCSqGSIb3DQEBBQUAMIGUMRYwFAYD
VQQDEw1YQkUgU2VydmVyIENBMQswCQYDVQQGEwJERTEYMBYGA1UECBMPUmhlaW5s
YW5kLVBmYWx6MRcwFQYDVQQHEw5LYWlzZXJzbGF1dGVybjEYMBYGA1UEChMPRnJh
dW5ob2ZlciBJVFdNMSAwHgYJKoZIhvcNAQkBFhFwZXRyeUBpdHdtLmZoZy5kZTAe
Fw0wNzAyMTUyMDI1MTNaFw0xMjAyMTQyMDI1MTNaMIGUMRYwFAYDVQQDEw1YQkUg
U2VydmVyIENBMQswCQYDVQQGEwJERTEYMBYGA1UECBMPUmhlaW5sYW5kLVBmYWx6
MRcwFQYDVQQHEw5LYWlzZXJzbGF1dGVybjEYMBYGA1UEChMPRnJhdW5ob2ZlciBJ
VFdNMSAwHgYJKoZIhvcNAQkBFhFwZXRyeUBpdHdtLmZoZy5kZTCCASIwDQYJKoZI
hvcNAQEBBQADggEPADCCAQoCggEBAMLqQ5C4dKKn6ZHLF4ru25zxGImY9DHnxN+H
KAn3rXqt6G9LNR4oYFwBBzA3so/YIQ7gZ01bH0IwpRWH4HjpP2MdXB8ve92HHhRG
TXZLmbZbs0QmdCT3b3VFQlTVHZyRUAPd8iKDsAuiZU/fgLCuksAtzHEAk0BOlOcf
uQuDZI/tRTfiFEuO5dYbrXKR1opReVfwyYM5kYTuxbrXMUkwdWEnSORYlvICLKbi
ua6e/hWhDSrj4C0x9FeCPCxY1FH9cneYKPBSWpCkwRrVppzqMW6Acgi2j/FEf2cd
80J4EXIDXO/Bsmf0b8K8ksaC4FnRVB0qWhgSFJ/cCWyRXvhNDr8CAwEAAaOB/DCB
+TAdBgNVHQ4EFgQUpmYMZrrku7FzZI8r8MjLiRyNYL8wgckGA1UdIwSBwTCBvoAU
pmYMZrrku7FzZI8r8MjLiRyNYL+hgZqkgZcwgZQxFjAUBgNVBAMTDVhCRSBTZXJ2
ZXIgQ0ExCzAJBgNVBAYTAkRFMRgwFgYDVQQIEw9SaGVpbmxhbmQtUGZhbHoxFzAV
BgNVBAcTDkthaXNlcnNsYXV0ZXJuMRgwFgYDVQQKEw9GcmF1bmhvZmVyIElUV00x
IDAeBgkqhkiG9w0BCQEWEXBldHJ5QGl0d20uZmhnLmRlggkA3Tklhwy1/bMwDAYD
VR0TBAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAZS2LQ74HvzpURIZ6BSC8G1va
e6fR+AT/lPZUc/VXUOSO883ZISonGhkresnLlM5xxOvQef/XY5OXmmPy6tUUIKOb
5+MnnAfgFr6cxfd+/VVS3rqpNi/yghQFhKzbdZZQYEbV8kkAUIHL4EI0MxE7f0OC
XINlEZCV3+wJlxf+Rir6aKhTiG4MA8hqzBnwEKHaO291YTDBfNcwuhUjAjC6ILiR
dEfPwRQkFToDKOymJ3glGGqPjefkpdmRcV+FepWrQkFA5G2JfNR9FBWjD1QM20k1
MjRUS/GiwXtJbm4VMHvyVlG8Wlq3Zfa+NOH/51kPixe0zoj0IgOBHkSEr+GHxw==
-----END CERTIFICATE-----
"""

    cert_as_der = """\
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
9sEYp1OU"""

    cert_as_der_stack = """\
MIIE5jCCBOIwggPKoAMCAQICAQIwDQYJKoZIhvcNAQEFBQAwgZQxFjAUBgNVBAMT
DVhCRSBTZXJ2ZXIgQ0ExCzAJBgNVBAYTAkRFMRgwFgYDVQQIEw9SaGVpbmxhbmQt
UGZhbHoxFzAVBgNVBAcTDkthaXNlcnNsYXV0ZXJuMRgwFgYDVQQKEw9GcmF1bmhv
ZmVyIElUV00xIDAeBgkqhkiG9w0BCQEWEXBldHJ5QGl0d20uZmhnLmRlMB4XDTA3
MDIxNTIwMzU1MloXDTA4MDIxNTIwMzU1MlowgYsxCzAJBgNVBAYTAkRFMRgwFgYD
VQQIEw9SaGVpbmxhbmQtUGZhbHoxGDAWBgNVBAoTD0ZyYXVuaG9mZXIgSVRXTTEQ
MA4GA1UECxMHUGVyc29uczEUMBIGA1UEAxMLdGVzdCB1c2VyIDExIDAeBgkqhkiG
9w0BCQEWEXBldHJ5QGl0d20uZmhnLmRlMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A
MIIBCgKCAQEAxCpuyK8ZCuZZhJoB26XJw9lPMEvaYE6qZHWxGwRJFZUPaUDOlMTq
pp3IfGjUySbPKxsId+9sn/6vQImwUo5fq3jqWx98nLdhAj0nypHcRBxWUM9aXhAS
vhdflHUHUpmEnmp6dnz+9Co4sduCOHvErRRMBFV6ZlxuPekc1W2uXCjK3QX/oDIP
BzqwPsnhQw/CGjvL8UDKhLKt3lRax/8qUC+6D32MDbR46WfHKOscIApy/tvCsKvi
lJV5bRSifBXf8mantXXCq4TVfJLbRWCuowvrtOwIpissOYn2E4Nb5e/ufIcmo2QU
a9jN8VVQX55nQPtog+MLjekcQS+rERj0BwIDAQABo4IBRDCCAUAwCQYDVR0TBAIw
ADAdBgNVHQ4EFgQUd4TE1K12g2SelixA5RrHR27Wf5swgckGA1UdIwSBwTCBvoAU
pmYMZrrku7FzZI8r8MjLiRyNYL+hgZqkgZcwgZQxFjAUBgNVBAMTDVhCRSBTZXJ2
ZXIgQ0ExCzAJBgNVBAYTAkRFMRgwFgYDVQQIEw9SaGVpbmxhbmQtUGZhbHoxFzAV
BgNVBAcTDkthaXNlcnNsYXV0ZXJuMRgwFgYDVQQKEw9GcmF1bmhvZmVyIElUV00x
IDAeBgkqhkiG9w0BCQEWEXBldHJ5QGl0d20uZmhnLmRlggkA3Tklhwy1/bMwSAYJ
YIZIAYb4QgEEBDsWOWh0dHA6Ly94ZW4tby1tYXRpYy5pdHdtLmZocmcuZnJhdW5o
b2Zlci5kZS94YmUvY2EtY3JsLnBlbTANBgkqhkiG9w0BAQUFAAOCAQEAFcWjp7rM
tZLuxiPyQRt7tsT12iME/vmsXGBSPg8/05o0JVaeuChyD81X+LMi+8pY4llokHcu
mJ24jV7qzf+XXwN5o024tpRqF4ampYLVRQi1XEu2A8T2MpG9/YLq5y1H2V3Iv6TM
mfRZ65V15OM5/d7xSI1ryZapJjp7Y14H9H/4WozcA+zJaPurVg3Zo+JDu8s6N/OD
1VfvjUWcmyE/Xabzh0MH3BcbBkYvMDqIJhZefU8kWgfY97ViZ9qMXQX/ADE1lhTL
0B9t1R58/bGeOHwYthv2jVsJemQCWzspwssjR5ONXQ9dIvjzAKYzcKsuC+19LDhj
fVjU2fbBGKdTlA=="""

    priv_key = """\
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

    self_signed_cert = """\
-----BEGIN CERTIFICATE-----
MIIC2zCCAkSgAwIBAgIJAOK8KJHbgdY4MA0GCSqGSIb3DQEBBQUAMFMxEzARBgoJ
kiaJk/IsZAEZFgNjb20xFzAVBgoJkiaJk/IsZAEZFgdleGFtcGxlMRMwEQYKCZIm
iZPyLGQBGRYDeGJlMQ4wDAYDVQQDEwVwZXRyeTAeFw0wNzAyMTIxMTM2MzNaFw0w
ODAyMTIxMTM2MzNaMFMxEzARBgoJkiaJk/IsZAEZFgNjb20xFzAVBgoJkiaJk/Is
ZAEZFgdleGFtcGxlMRMwEQYKCZImiZPyLGQBGRYDeGJlMQ4wDAYDVQQDEwVwZXRy
eTCBnzANBgkqhkiG9w0BAQEFAAOBjQAwgYkCgYEAznDGQTzTpSnjH8j0p2I7RUvz
sqpRbhQDTzt6tFszcX316jPdXvsdbWcv9kzM95uKeFlsmD1/KIgfDrBylhWKHeez
+WIXrM9l8vEW2VBGke/6cHcJvgSoLGMSrNTNqrxlnzLuwrj/jXSWS06KduLV0Aeo
7mtyzeQL79Iwxrr66IsCAwEAAaOBtjCBszAdBgNVHQ4EFgQUPvZni4gYm82ak0m6
3RA0Ghs9rLMwgYMGA1UdIwR8MHqAFD72Z4uIGJvNmpNJut0QNBobPayzoVekVTBT
MRMwEQYKCZImiZPyLGQBGRYDY29tMRcwFQYKCZImiZPyLGQBGRYHZXhhbXBsZTET
MBEGCgmSJomT8ixkARkWA3hiZTEOMAwGA1UEAxMFcGV0cnmCCQDivCiR24HWODAM
BgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4GBAHvVyRXhYqT/g2gstP+YWzho
JEYCydQJlj4jvqkTw/J4A0wBByIy6y9VLRl6oahsZKq1f5M/t4jxyJ1RzGigSoYH
D1ErglF1EXFuUtvmCBlOLvmnIQTy+G674/4a1lwiqB30L60w5oPoEMt0HtWfqysV
Yj30VN3oen0CEF/RMt8D
-----END CERTIFICATE-----
"""
    
class TestCertificate(unittest.TestCase):

    def setUp(self):

        self.ca = X509Certificate.load(ExampleData.ca_cert)
        
    def test_load(self):
	"""Tests whether loading from file works."""
	try:
            ExampleData.get_sample_cert()
	except Exception:
	    self.fail("sample certificate could not be built.")

    def test_signing(self):
	"""Tests whether siging as such works."""
	cert = ExampleData.get_sample_cert()
	sig = cert.msg_signature(ExampleData.text)
	self.assertEqual(ExampleData.text_sig, sig)

    def test_validate(self):
	cert = ExampleData.get_sample_cert()
	try:
	    cert.msg_validate(ExampleData.text, ExampleData.text_sig)
	except Exception:
	    self.fail("validation failed")

    def test_ca(self):
        self.assertTrue(self.ca.is_CA())

    def test_nonca(self):
        nonca_cert = ExampleData.get_sample_cert()
        self.assertFalse(nonca_cert.is_CA())

    def test_ca_validate(self):
        cert = ExampleData.get_sample_cert()
        self.assertTrue(self.ca.validate_certificate(cert))

    def test_ca_nonvalidate(self):
        self_signed = X509Certificate.load(ExampleData.self_signed_cert)
        self.assertFalse(self.ca.validate_certificate(self_signed))
        
    def test_both(self):
	cert = ExampleData.get_sample_cert()

	test_data = "hello world!"
	sig = cert.msg_signature(test_data)
	try:
	    cert.msg_validate(test_data, sig)
	except Exception:
	    self.fail("validation failed")

    def test_load_der(self):
        cert = ExampleData.get_sample_cert()
        der_string = cert.as_der()
        import base64
        cert_from_der = X509Certificate.load_der(ExampleData.cert_as_der_stack)
        self.assertEqual(der_string, cert_from_der.as_der())

class TestSecurityLayer(unittest.TestCase):

    def setUp(self):
        self.cert = ExampleData.get_sample_cert()
        self.ca = X509Certificate.load(ExampleData.ca_cert)
        self.msg = self.__build_sample_message()

    def tearDown(self):
        pass

    def __build_empty_message(self):
        m = etree.Element(XBE("Message"), nsmap={"xbe": str(XBE)})
        return m
        
    def __build_no_body_message(self):
        m = self.__build_empty_message()
        hdr = etree.SubElement(m, XBE("MessageHeader"))
        return m

    def __build_empty_body_message(self):
        m = self.__build_no_body_message()
        bod = etree.SubElement(m, XBE("MessageBody"))
        return m
    
    def __build_sample_message(self):
        m = self.__build_empty_body_message()
        bod = m.find(XBE("MessageBody"))
        etree.SubElement(bod, "TestData").text = \
                              """The quick brown fox jumps over the lazy dog"""
        return m

    def test_sign(self):
        pipe = X509SecurityLayer(self.cert, self.cert, [])
        msg, sig = pipe.sign(self.msg)
        expected_sig = "fLKOiUJUc2ZpOpELRYFK0woiH5l8z4CHiArnOYH5sr1EO3PLx+SpfDaY9kUPE7m3gXQSZjlWPm/9LkeGTKYyZyLA4xuL/Jma9kpCZplW6A38HyJzxek5E4lq1gtDjaIlvrA4bGgLFWF8rljIxX+T4O3QQvvRAeXTSs3pxeRJ+ioYxaN8/TfNLS93oN159EsgT5ZHjtdT8NjlyAft7uL7ZsllAgxQmoRiM+mD4BmQp1eEmwq28sp0ssaP2xat9K7pjG4Fxsq15FV1m7fbAMi52Qp5aRb8+nboaA7Xt6A2HUH2vT2Sl1n76K01qXv5SIdj/Zt9f3BV+e0OogOzqv5jIg=="
        self.assertEqual(expected_sig, sig)

    def test_validate(self):
        pipe = X509SecurityLayer(self.cert, self.cert, [self.ca]) # encrypt to myself
        recv_msg = pipe.validate(pipe.sign(self.msg))

    def test_novalidate_noca(self):
        pipe = X509SecurityLayer(self.cert, None, [])
        try:
            recv_msg = pipe.validate(pipe.sign(self.msg))
        except ValidationError, ve:
            pass
        else:
            self.fail("ValidationError expected")

    def test_novalidate_not_signed_by_ca(self):
        cert = X509Certificate.load(ExampleData.self_signed_cert,
                                    ExampleData.priv_key)
        pipe = X509SecurityLayer(cert, None, [self.ca])
        try:
            recv_msg = pipe.validate(pipe.sign(self.msg, include_certificate=True))
        except ValidationError, ve:
            pass
        else:
            self.fail("ValidationError expected")

    def test_noinclude_cert(self):
        pipe = X509SecurityLayer(self.cert, None, [self.ca])
        send_msg = pipe.sign(self.msg, include_certificate=False)[0]
        try:
            recv_msg = pipe.validate(send_msg)
        except ValidationError, ve:
            pass
        else:
            self.fail("ValidationError expected")

    def test_include_cert(self):
        pipe = X509SecurityLayer(self.cert, None, [self.ca])
        send_msg = pipe.sign(self.msg, include_certificate=True)[0]
        try:
            recv_msg = pipe.validate(send_msg)
        except ValidationError, ve:
            self.fail("ValidationError should not occur, since certificate has been included.")
        else:
            pass

    def test_validate_decrypt_empty_body(self):
        pipe = X509SecurityLayer(self.cert, self.cert, [self.ca]) # encrypt to myself
        msg = self.__build_empty_body_message()
        recv_msg = pipe.validate_and_decrypt(
            pipe.sign_and_encrypt(msg))
        # compare only the body
        b_sent = msg.find(XBE("MessageBody"))
        b_recv = recv_msg.find(XBE("MessageBody"))
        self.assertEqual(etree.tostring(b_sent), etree.tostring(b_recv))

    def test_validate_decrypt_no_body(self):
        pipe = X509SecurityLayer(self.cert, self.cert, [self.ca]) # encrypt to myself
        msg = self.__build_no_body_message()
        recv_msg = pipe.validate_and_decrypt(
            pipe.sign_and_encrypt(msg))

        # compare only the body
        b_sent = msg.find(XBE("MessageBody"))
        b_recv = recv_msg.find(XBE("MessageBody"))
        self.assertTrue(b_sent == None and b_recv == None)
        
    def test_validate_decrypt_long_body(self):
        pipe = X509SecurityLayer(self.cert, self.cert, [self.ca]) # encrypt to myself
        msg = self.__build_empty_body_message()
        bod = msg.find(XBE("MessageBody"))
        bod.text = ExampleData.cert * 10

        enc_msg = pipe.sign_and_encrypt(msg)
        recv_msg = pipe.validate_and_decrypt(enc_msg)

        # compare only the body
        b_sent = msg.find(XBE("MessageBody"))
        b_recv = recv_msg.find(XBE("MessageBody"))
        self.assertEqual(etree.tostring(b_sent), etree.tostring(b_recv))

class TestCipher(unittest.TestCase):
    def setUp(self):
        self.cert = ExampleData.get_sample_cert()
        self.ca = X509Certificate.load(ExampleData.ca_cert)

    def tearDown(self):
        pass

    def test_cipher_encrypt(self):
        enc = Cipher(key="01234", IV="0", do_encryption=True)
        expected = "Eaes3PgLelEOzQTyf8VBXuurFkeqOnKEfCL+hMi6JPq0UsT7Lj8oWY4w8E/W+8yU"
        encrypted = base64.b64encode(enc(ExampleData.text))
        self.assertEqual(expected, encrypted)

    def test_cipher_decrypt(self):
        expected = ExampleData.text
        encrypted = "Eaes3PgLelEOzQTyf8VBXuurFkeqOnKEfCL+hMi6JPq0UsT7Lj8oWY4w8E/W+8yU"
        dec = Cipher(key="01234", IV="0", do_encryption=False)
        decrypted = dec(base64.b64decode(encrypted))
        self.assertEqual(expected, decrypted)

    def test_cipher_encrypt_decrypt(self):
        long_data = ExampleData.cert * 10
        enc = Cipher(do_encryption=True)
        dec = Cipher(key=enc.key(), do_encryption=False)
        self.assertEqual(long_data, dec(enc(long_data)))
        

def suite():
    s1 = unittest.makeSuite(TestCertificate, 'test')
    s2 = unittest.makeSuite(TestSecurityLayer, 'test')
    s3 = unittest.makeSuite(TestCipher, 'test')
    return unittest.TestSuite((s1,s2,s3))

if __name__ == '__main__':
    unittest.main()
