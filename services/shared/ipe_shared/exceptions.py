class IPEError(Exception):
    """Base exception for all IPE errors."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(IPEError):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__("AUTHENTICATION_FAILED", message)


class AuthorizationError(IPEError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__("UNAUTHORIZED", message)


class ValidationError(IPEError):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__("VALIDATION_ERROR", message, details)


class NotFoundError(IPEError):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__("NOT_FOUND", f"{entity_type} '{entity_id}' not found")


class TenantMismatchError(IPEError):
    def __init__(self):
        super().__init__("TENANT_MISMATCH", "Resource does not belong to current tenant")


class DatabaseError(IPEError):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__("DATABASE_ERROR", message)


class KafkaError(IPEError):
    def __init__(self, message: str = "Kafka operation failed"):
        super().__init__("KAFKA_ERROR", message)
