"""Password hashing utilities using bcrypt."""
import bcrypt


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password as string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password to verify against

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
