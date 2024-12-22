from app.database.models import async_session
from app.database.models import User
from sqlalchemy import select, update

async def set_user(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.flush()
            await session.commit()


async def update_data_permission(tg_id, permission: bool):
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.tg_id == tg_id)
            .values(data_permission=permission)
        )
        await session.commit()

async def update_user_data(tg_id, name: str, phone_number: str, inn: str):
    async with async_session() as session:
        # Выполняем запрос на обновление данных пользователя
        await session.execute(
            update(User)
            .where(User.tg_id == tg_id)
            .values(
                user_name=name,
                phone_number=phone_number,
                inn=inn
            )
        )
        await session.commit()