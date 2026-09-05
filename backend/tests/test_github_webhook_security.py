import hmac

from app.services.github.webhook_security import calculate_signature, verify_signature


def test_calculates_hmac_sha256_signature_with_known_secret_and_payload() -> None:
    secret = "unit-test-secret"
    payload = b'{"zen":"Keep it logically awesome."}'

    signature = calculate_signature(secret, payload)

    assert signature == "sha256=e9f2d1a86178b177d82dfa7ff405f573a1dd799319522369363576fdf77c6003"


def test_verify_signature_accepts_valid_signature() -> None:
    secret = "unit-test-secret"
    payload = b'{"hook_id":123}'

    assert verify_signature(secret, payload, calculate_signature(secret, payload)) is True


def test_verify_signature_rejects_invalid_signature() -> None:
    secret = "unit-test-secret"
    payload = b'{"hook_id":123}'
    invalid_signature = "sha256=" + ("0" * 64)

    assert hmac.compare_digest(invalid_signature, calculate_signature(secret, payload)) is False
    assert verify_signature(secret, payload, invalid_signature) is False


def test_verify_signature_requires_sha256_prefix() -> None:
    assert verify_signature("unit-test-secret", b"{}", "0" * 64) is False
