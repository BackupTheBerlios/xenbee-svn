"""Exceptions concerning security."""

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

