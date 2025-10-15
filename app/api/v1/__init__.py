from .auth import router as auth_router
from .users import router as users_router
from .roles import router as roles_router
from .permissions import router as permissions_router
from .oauth import router as oauth_router
from .jwt_keys import router as jwt_keys_router
from .language import router as language_router

__all__ = [
    "auth_router",
    "users_router", 
    "roles_router",
    "permissions_router",
    "oauth_router",
    "jwt_keys_router",
    "language_router"
] 