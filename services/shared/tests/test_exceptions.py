import pytest

from ipe_shared.exceptions import (
    IPEError,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    NotFoundError,
    TenantMismatchError,
    DatabaseError,
    KafkaError,
)


class TestExceptions:
    def test_ipe_error_base(self):
        err = IPEError(code="TEST_ERROR", message="Something went wrong", details={"key": "val"})
        assert err.code == "TEST_ERROR"
        assert err.message == "Something went wrong"
        assert err.details == {"key": "val"}

    def test_authentication_error(self):
        err = AuthenticationError()
        assert err.code == "AUTHENTICATION_FAILED"
        assert err.message == "Authentication failed"

    def test_authentication_error_custom_message(self):
        err = AuthenticationError("Token invalid")
        assert err.message == "Token invalid"

    def test_authorization_error(self):
        err = AuthorizationError()
        assert err.code == "UNAUTHORIZED"
        assert err.message == "Insufficient permissions"

    def test_validation_error(self):
        err = ValidationError("Invalid field", details={"field": "email"})
        assert err.code == "VALIDATION_ERROR"
        assert err.details == {"field": "email"}

    def test_not_found_error(self):
        err = NotFoundError("Product", "PRD-001")
        assert err.code == "NOT_FOUND"
        assert "PRD-001" in err.message

    def test_tenant_mismatch_error(self):
        err = TenantMismatchError()
        assert err.code == "TENANT_MISMATCH"

    def test_database_error(self):
        err = DatabaseError()
        assert err.code == "DATABASE_ERROR"

    def test_kafka_error(self):
        err = KafkaError()
        assert err.code == "KAFKA_ERROR"

    def test_all_exception_types_are_ipe_error_subclasses(self):
        assert issubclass(AuthenticationError, IPEError)
        assert issubclass(AuthorizationError, IPEError)
        assert issubclass(ValidationError, IPEError)
        assert issubclass(NotFoundError, IPEError)
        assert issubclass(TenantMismatchError, IPEError)
        assert issubclass(DatabaseError, IPEError)
        assert issubclass(KafkaError, IPEError)
