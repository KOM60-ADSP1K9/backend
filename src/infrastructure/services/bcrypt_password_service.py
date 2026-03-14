"""
Password hashing service using bcrypt.
"""

import bcrypt

from src.application.i_password_service import IPasswordService


class BcryptPasswordService(IPasswordService):
    """Bcrypt-backed password hashing."""

    def hash(self, plain_password: str) -> str:
        hashed = bcrypt.hashpw(
            plain_password.encode("utf-8"),
            bcrypt.gensalt(),
        )
        return hashed.decode("utf-8")

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
