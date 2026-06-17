from uuid import UUID

from sqlalchemy import ColumnExpressionArgument
from sqlalchemy.orm import declared_attr

from ipe_shared.middleware.tenant_context import tenant_ctx


class TenantScopedMixin:
    @declared_attr
    def tenant_id(cls):
        from sqlalchemy import Column
        from sqlalchemy.dialects.postgresql import UUID as PG_UUID

        return Column("tenant_id", PG_UUID, nullable=False)

    @classmethod
    def tenant_filter(cls) -> ColumnExpressionArgument:
        current_tenant = tenant_ctx.get()
        if current_tenant:
            return cls.tenant_id == UUID(current_tenant)
        return cls.tenant_id.isnot(None)
