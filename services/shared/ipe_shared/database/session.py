from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ipe_shared.database.connection import get_engine
from ipe_shared.middleware.tenant_context import tenant_ctx


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    engine = get_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        tid = tenant_ctx.get()
        if tid:
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, false)"),
                {"tid": str(tid)},
            )
        yield session
