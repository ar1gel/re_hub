from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User, WbAccount


async def get_or_create_user(session: AsyncSession, tg_id: int, username: str | None, full_name: str | None) -> User:
    result = await session.execute(select(User).where(User.id == tg_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=tg_id, username=username, full_name=full_name)
        session.add(user)
        await session.commit()
    else:
        if user.username != username or user.full_name != full_name:
            user.username = username
            user.full_name = full_name
            await session.commit()
    return user


async def get_accounts(session: AsyncSession, tg_id: int) -> list[WbAccount]:
    result = await session.execute(
        select(WbAccount).where(WbAccount.user_id == tg_id, WbAccount.is_active == True)
    )
    return list(result.scalars().all())


async def get_account_by_id(session: AsyncSession, account_id: int, tg_id: int) -> WbAccount | None:
    result = await session.execute(
        select(WbAccount).where(WbAccount.id == account_id, WbAccount.user_id == tg_id, WbAccount.is_active == True)
    )
    return result.scalar_one_or_none()


async def add_account(session: AsyncSession, tg_id: int, name: str, token: str) -> WbAccount:
    account = WbAccount(user_id=tg_id, name=name, token=token)
    session.add(account)
    await session.commit()
    return account


async def delete_account(session: AsyncSession, account_id: int, tg_id: int) -> bool:
    result = await session.execute(
        select(WbAccount).where(WbAccount.id == account_id, WbAccount.user_id == tg_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        return False
    account.is_active = False
    await session.commit()
    return True
