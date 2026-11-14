class DomainError(Exception):
    """Base de todos los errores de negocio."""
    pass


class NotFoundError(DomainError):
    """Recurso no encontrado -> 404."""
    pass


class UnauthorizedError(DomainError):
    """Credenciales inválidas o token malo -> 401."""
    pass


class ForbiddenError(DomainError):
    """Sin permisos para la operación -> 403."""
    pass
