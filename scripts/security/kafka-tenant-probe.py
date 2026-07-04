#!/usr/bin/env python3
from ipe_shared.config import settings
from ipe_shared.events.consumer import resolve_consumer_tenant_id, get_consumer_group

t = resolve_consumer_tenant_id()
print("KAFKA_CONSUMER_TENANT_ID:", repr(settings.KAFKA_CONSUMER_TENANT_ID))
print("resolved:", t)
print("group:", get_consumer_group("fea-svc", t) if t else "unscoped")
