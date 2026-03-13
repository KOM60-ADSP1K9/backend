from datetime import datetime, timezone, timedelta
from uuid import UUID

import jwt
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from src.core.config import settings
from src.core.exceptions import AuthenticationException
from src.domain.entity.user import User
from src.application.i_token_service import TokenPayload, ITokenService

_EMAIL_SALT = settings.EMAIL_SALT


class JWTTokenService(ITokenService):
    """Concrete JWT implementation backed by HMAC-SHA512."""

    def __init__(self) -> None:
        self._secret = settings.JWT_SECRET_KEY
        self._algorithm = settings.JWT_ALGORITHM
        self._expires_minutes = settings.JWT_EXPIRES_MINUTES

    def create_access_token(self, user: User) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "iat": now,
            "exp": now + timedelta(minutes=self._expires_minutes),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_token(self, token: str) -> TokenPayload:
        try:
            data = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise AuthenticationException("Token has expired") from exc
        except jwt.InvalidTokenError as exc:
            raise AuthenticationException("Invalid token") from exc

        return TokenPayload(
            user_id=UUID(data["sub"]),
            email=data["email"],
            role=data["role"],
        )

    # ── Email-verification tokens (itsdangerous) ────

    def generate_verification_token(self, email: str) -> str:
        """Create a signed, time-limited token that encodes the user's email."""
        s = URLSafeTimedSerializer(settings.VERIFICATION_SECRET_KEY)
        return s.dumps(email, salt=_EMAIL_SALT)

    def verify_email_token(
        self, token: str, expiration_seconds: int | None = None
    ) -> str:
        """Verify and decode the token, returning the email it contains."""
        max_age = expiration_seconds or settings.JWT_EXPIRES_MINUTES * 60
        s = URLSafeTimedSerializer(settings.VERIFICATION_SECRET_KEY)
        try:
            email: str = s.loads(token, salt=_EMAIL_SALT, max_age=max_age)
        except SignatureExpired as exc:
            raise AuthenticationException("Token has expired") from exc
        except BadSignature as exc:
            raise AuthenticationException("Invalid verification token") from exc
        return email
