from enum import StrEnum


class DemandType(StrEnum):
    MAKE_TO_ORDER = "MTO"
    MAKE_TO_STOCK = "MTS"
    CONFIGURE_TO_ORDER = "CTO"
    ENGINEER_TO_ORDER = "ETO"


class MOStatus(StrEnum):
    DRAFT = "draft"
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderStatus(StrEnum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    HOLD = "hold"
    CANCELLED = "cancelled"


class AutonomyMode(StrEnum):
    SHADOW = "shadow"
    SUGGEST = "suggest"
    AUTONOMOUS = "autonomous"


class SupplyStatus(StrEnum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class DelayCategory(StrEnum):
    MATERIAL_SHORTAGE = "material_shortage"
    CAPACITY_OVERLOAD = "capacity_overload"
    LABOR_ABSENCE = "labor_absence"
    SUPPLIER_DELAY = "supplier_delay"
    MAINTENANCE = "maintenance"
    QUALITY_ISSUE = "quality_issue"
    PROCESS_VARIANCE = "process_variance"
    OTHER = "other"


class TenantTier(StrEnum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class ResolutionStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50
