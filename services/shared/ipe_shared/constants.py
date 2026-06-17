from enum import Enum


class DemandType(str, Enum):
    MAKE_TO_ORDER = "MTO"
    MAKE_TO_STOCK = "MTS"
    CONFIGURE_TO_ORDER = "CTO"
    ENGINEER_TO_ORDER = "ETO"


class MOStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    HOLD = "hold"
    CANCELLED = "cancelled"


class AutonomyMode(str, Enum):
    SHADOW = "shadow"
    SUGGEST = "suggest"
    AUTONOMOUS = "autonomous"


class SupplyStatus(str, Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


class DelayCategory(str, Enum):
    MATERIAL_SHORTAGE = "material_shortage"
    CAPACITY_OVERLOAD = "capacity_overload"
    LABOR_ABSENCE = "labor_absence"
    SUPPLIER_DELAY = "supplier_delay"
    MAINTENANCE = "maintenance"
    QUALITY_ISSUE = "quality_issue"
    PROCESS_VARIANCE = "process_variance"
    OTHER = "other"


class TenantTier(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class ResolutionStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


MAX_PAGE_SIZE = 200
DEFAULT_PAGE_SIZE = 50
