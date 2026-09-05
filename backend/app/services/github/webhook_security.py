import hashlib
import hmac
import re

SIGNATURE_PREFIX = "sha256="
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


def calculate_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def verify_signature(secret: str, body: bytes, signature_header: str) -> bool:
    if not secret.strip() or not signature_header.startswith(SIGNATURE_PREFIX):
        return False

    signature = signature_header.removeprefix(SIGNATURE_PREFIX)
    if SHA256_HEX_PATTERN.fullmatch(signature) is None:
        return False

    expected_signature = calculate_signature(secret, body)
    return hmac.compare_digest(expected_signature, signature_header)
