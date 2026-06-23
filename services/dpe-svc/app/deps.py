from ipe_shared.middleware.tenant_context import tenant_ctx


async def get_current_tenant() -> str:
    tid = tenant_ctx.get()
    return str(tid) if tid else ""