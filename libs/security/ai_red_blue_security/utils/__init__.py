"""Security utilities for encoding, decoding, and payload generation."""

import base64
import hashlib
import json
import random
import string
from typing import Optional

# Note: For authorized security research and defensive purposes only


def encode_payload(data: bytes, encoding: str = "base64") -> str:
    """Encode binary data to string format.

    Args:
        data: Binary data to encode
        encoding: Encoding format (base64, hex)

    Returns:
        Encoded string
    """
    if encoding == "base64":
        return base64.b64encode(data).decode("utf-8")
    elif encoding == "hex":
        return data.hex()
    elif encoding == "url":
        return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")
    else:
        raise ValueError(f"Unsupported encoding: {encoding}")


def decode_payload(encoded: str, encoding: str = "base64") -> bytes:
    """Decode string to binary data.

    Args:
        encoded: Encoded string
        encoding: Encoding format (base64, hex, url)

    Returns:
        Decoded binary data
    """
    try:
        if encoding == "base64":
            padding = 4 - len(encoded) % 4
            if padding != 4:
                encoded += "=" * padding
            return base64.b64decode(encoded)
        elif encoding == "hex":
            return bytes.fromhex(encoded)
        elif encoding == "url":
            padding = 4 - len(encoded) % 4
            if padding != 4:
                encoded += "=" * padding
            return base64.urlsafe_b64decode(encoded)
        else:
            raise ValueError(f"Unsupported encoding: {encoding}")
    except Exception:
        raise ValueError(f"Failed to decode payload with {encoding}")


def generate_shellcode(
    length: int = 128,
    charset: Optional[str] = None,
) -> bytes:
    """Generate random shellcode-like bytes for testing.

    Args:
        length: Number of bytes to generate
        charset: Custom character set or None for random bytes

    Returns:
        Random byte sequence
    """
    if charset:
        return "".join(random.choices(charset, k=length)).encode("utf-8")
    else:
        return bytes(random.randint(0, 255) for _ in range(length))


def xor_encrypt(data: bytes, key: bytes) -> bytes:
    """XOR encrypt/decrypt data.

    Args:
        data: Data to encrypt
        key: Encryption key

    Returns:
        XOR encrypted data
    """
    result = bytearray(len(data))
    for i in range(len(data)):
        result[i] = data[i] ^ key[i % len(key)]
    return bytes(result)


def xor_decrypt(encrypted: bytes, key: bytes) -> bytes:
    """XOR decrypt data (same as encryption).

    Args:
        encrypted: Encrypted data
        key: Decryption key

    Returns:
        Decrypted data
    """
    return xor_encrypt(encrypted, key)


def calculate_checksum(data: bytes, algorithm: str = "sha256") -> str:
    """Calculate checksum/hash of data.

    Args:
        data: Data to hash
        algorithm: Hash algorithm (md5, sha1, sha256, sha512)

    Returns:
        Hex digest of hash
    """
    hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def generate_fingerprint(data: bytes) -> dict[str, str]:
    """Generate multiple fingerprints for data.

    Args:
        data: Data to fingerprint

    Returns:
        Dictionary of hashes
    """
    return {
        "md5": calculate_checksum(data, "md5"),
        "sha1": calculate_checksum(data, "sha1"),
        "sha256": calculate_checksum(data, "sha256"),
        "sha512": calculate_checksum(data, "sha512"),
    }


def validate_sha256(checksum: str, data: bytes) -> bool:
    """Validate SHA256 checksum.

    Args:
        checksum: Expected checksum
        data: Data to validate

    Returns:
        True if checksum matches
    """
    return calculate_checksum(data, "sha256") == checksum.lower()


class SafetyChecker:
    """Check if payloads or techniques are safe for testing."""

    KNOWN_DANGEROUS_PATTERNS = [
        b"rm -rf",
        b"format c:",
        b"del /s /q",
        b"mkfs",
    ]

    @classmethod
    def check(cls, data: bytes) -> tuple[bool, list[str]]:
        """Check data for dangerous patterns.

        Args:
            data: Data to check

        Returns:
            Tuple of (is_safe, list of warnings)
        """
        warnings = []
        data_lower = data.lower()

        for pattern in cls.KNOWN_DANGEROUS_PATTERNS:
            if pattern in data_lower:
                warnings.append(f"Dangerous pattern detected: {pattern.decode('utf-8', errors='ignore')}")

        return len(warnings) == 0, warnings


def check_safety(data: bytes) -> dict:
    """Check if data contains dangerous patterns.

    Args:
        data: Data to check

    Returns:
        Dictionary with is_safe and warnings
    """
    is_safe, warnings = SafetyChecker.check(data)
    return {
        "is_safe": is_safe,
        "warnings": warnings,
        "patterns_checked": len(SafetyChecker.KNOWN_DANGEROUS_PATTERNS),
    }


def random_string(length: int, charset: str = string.ascii_letters + string.digits) -> str:
    """Generate a random string.

    Args:
        length: Length of string
        charset: Character set to use

    Returns:
        Random string
    """
    return "".join(random.choices(charset, k=length))


def json_minify(data: str) -> str:
    """Minify JSON string.

    Args:
        data: JSON string to minify

    Returns:
        Minified JSON
    """
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, separators=(",", ":"))
    except json.JSONDecodeError:
        return data


class SecurityUtils:
    """Utility class for security operations."""

    @staticmethod
    def encode_payload(data: bytes, encoding: str = "base64") -> str:
        return encode_payload(data, encoding)

    @staticmethod
    def decode_payload(encoded: str, encoding: str = "base64") -> bytes:
        return decode_payload(encoded, encoding)

    @staticmethod
    def generate_fingerprint(data: bytes) -> dict[str, str]:
        return generate_fingerprint(data)

    @staticmethod
    def xor_encrypt(data: bytes, key: bytes) -> bytes:
        return xor_encrypt(data, key)

    @staticmethod
    def check_safety(data: bytes) -> dict:
        return check_safety(data)
