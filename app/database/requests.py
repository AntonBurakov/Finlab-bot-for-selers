from app.database.models import async_session
from app.database.models import User
from sqlalchemy import select, update, delete


async def set_user(tg_id: int):
    """Создает запись о пользователе, если его нет в БД"""
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()
            print(f"[INFO] Добавлен новый пользователь: {tg_id}")
        else:
            print(f"[INFO] Пользователь {tg_id} уже существует")


async def get_user(tg_id: int):
    """Возвращает данные пользователя по Telegram ID"""
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))


async def user_exists(tg_id: int) -> bool:
    """Проверяет, существует ли пользователь в БД"""
    return bool(await get_user(tg_id))


async def update_data_permission(tg_id: int, permission: bool):
    """Обновляет согласие пользователя на обработку ПД"""
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.tg_id == tg_id)
            .values(data_permission=permission)
        )
        await session.commit()
        print(f"[INFO] Обновлено согласие на ПД для {tg_id}: {permission}")


async def update_user_data(tg_id: int, name: str, phone_number: str, inn: str, marketplace_link: str):  
    """Обновляет персональные данные пользователя, включая ссылку на маркетплейс"""
    async with async_session() as session:
        await session.execute(
            update(User)
            .where(User.tg_id == tg_id)
            .values(
                user_name=name,
                phone_number=phone_number,
                inn=inn,
                marketplace_link=marketplace_link  
            )
        )
        await session.commit()
        print(f"[INFO] Данные пользователя {tg_id} обновлены, включая ссылку на маркетплейс")


async def delete_user(tg_id: int):
    """Удаляет пользователя и все его данные"""
    async with async_session() as session:
        await session.execute(delete(User).where(User.tg_id == tg_id))
        await session.commit()
        print(f"[INFO] Данные пользователя {tg_id} удалены")