from .v1 import (
    auth_router,
    users_router,
    roles_router,
    permissions_router,
    oauth_router,
    jwt_keys_router,
    language_router
)

__all__ = [
    "auth_router",
    "users_router",
    "roles_router", 
    "permissions_router",
    "oauth_router",
    "jwt_keys_router",
    "language_router"
] 