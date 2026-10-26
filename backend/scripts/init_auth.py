"""Generate a project-local development signing key; never prints key material."""

from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def main():
    target = Path(".secrets/access-private.pem")
    target.parent.mkdir(exist_ok=True)
    if target.exists():
        raise SystemExit("Key already exists; rotation requires an explicit plan")
    key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    target.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    target.chmod(0o600)
    print(
        "Development key generated. Set AUTH_PRIVATE_KEY_PATH=.secrets/access-private.pem "
        "in ignored .env."
    )
    print(
        "On Windows restrict the file ACL to your account; "
        "production keys belong in a secret manager."
    )


if __name__ == "__main__":
    main()
