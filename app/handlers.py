from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from unittest.mock import patch

import app.database.requests as rq
from app.scoring_utils.wildberries import fetch_wildberries_data
from app.scoring_utils.checko import fetch_checko_data
from app.scoring_utils.historical_excel import get_seller_data_from_excel
from app.scoring_utils.scoring_risks import RiskAnalysis
import requests
import json
import random  
import re
import html 

router = Router()

# 🔥 ИЗМЕНЕНИЕ: Явный API-ключ Yandex GPT (временно)
YANDEX_GPT_API_KEY = "AQVNzpC6YgzXzixqHMjlWioapUB9MSNhgD5xv9Br"  # ← Вставьте свой API-ключ здесь

class Scoring(StatesGroup):
    name = State()
    number = State()
    inn = State()
    marketplace_link = State()

### 📌 1. Запрос согласия перед регистрацией
@router.message(CommandStart())
async def start_command(message: Message):
    consent_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, согласен", callback_data="consent_granted")]
        ]
    )

    await message.answer(
        "Добро пожаловать в finalb помощник!\n"
        "Перед использованием бота, пожалуйста, дайте согласие на обработку персональных данных.",
        reply_markup=consent_markup
    )

@router.callback_query(lambda c: c.data == "consent_granted")
async def process_consent(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Записываем ID в БД ТОЛЬКО ПОСЛЕ СОГЛАСИЯ
    await rq.set_user(user_id)
    await rq.update_data_permission(user_id, True)  # Фиксируем согласие
    
    await callback_query.message.edit_text(
        "Спасибо за согласие! Теперь вы можете пользоваться ботом.\n\n"
        "Доступные команды:\n"
        "/scoring - Запуск скоринга\n"
        "/revoke_consent - Отозвать согласие и удалить данные"
    )
    await callback_query.answer()


### 📌 2. Обработчик отзыва согласия и удаления данных
@router.message(Command("revoke_consent"))
async def revoke_consent_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, удалить данные", callback_data="confirm_revoke")],
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_revoke")]
        ]
    )
    
    await message.answer(
        "Вы уверены, что хотите отозвать согласие на обработку персональных данных? "
        "Это действие удалит все ваши данные из системы!",
        reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data in ["confirm_revoke", "cancel_revoke"])
async def process_revoke(callback_query: CallbackQuery):
    if callback_query.data == "confirm_revoke":
        await rq.delete_user(callback_query.from_user.id)
        await callback_query.message.edit_text("Ваши данные успешно удалены. Вы можете снова зарегистрироваться в боте в любое время.")
    else:
        await callback_query.message.edit_text("Отмена удаления данных.")

    await callback_query.answer()


### 📌 3. Запрос скоринга только если есть согласие
@router.message(Command('scoring'))
async def register_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await rq.get_user(user_id)

    # Проверяем, есть ли пользователь и дал ли он согласие
    if not user or not user.data_permission:
        await message.answer("Вы не дали согласие на обработку персональных данных. Используйте /start, чтобы дать согласие.")
        return

    # Начинаем сбор данных (ФИО)
    await state.set_state(Scoring.name)
    await message.answer("Введите ваше ФИО")


### 📌 4. Сбор данных (ФИО, телефон, ИНН)
@router.message(Scoring.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Scoring.number)
    await message.answer('Введите ваш номер телефона')

@router.message(Scoring.number)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    await state.set_state(Scoring.inn)
    await message.answer('Введите ваш ИНН')



@router.message(Scoring.inn)
async def register_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text)
    await state.set_state(Scoring.marketplace_link)
    await message.answer("Введите ссылку на ваш профиль в маркетплейсе")



@router.message(Scoring.marketplace_link)
async def register_marketplace_link(message: Message, state: FSMContext):
    await state.update_data(marketplace_link=message.text)  # 🔥 Сохраняем ссылку
    data = await state.get_data()

    await rq.update_user_data(
        tg_id=message.from_user.id, 
        name=data.get("name"),  # Имя
        phone_number=data.get("number"),  # Номер телефона
        inn=data["inn"],  # ИНН
        marketplace_link=data["marketplace_link"]  # Добавляем ссылку
    )

    # **Получаем seller_id из marketplace_link**
    seller_id_match = re.search(r"/seller/(\d+)", data["marketplace_link"])
    if not seller_id_match:
        await message.answer("Ошибка: Не удалось извлечь seller_id из ссылки.")
        return

    seller_id = seller_id_match.group(1)

    # **Запрашиваем данные от Wildberries API**
    wildberries_data = await fetch_wildberries_data(seller_id)

    checko_data = await fetch_checko_data(data["inn"])

    excel_data = get_seller_data_from_excel("Истор данные.xlsx", data["marketplace_link"])

    # **Вывод данных пользователю**
    await message.answer(
        f"✅ Данные успешно собраны!\n\n"
        f"📌 <b>ФИО:</b> {data.get('name', 'Не указано')}\n"
        f"📌 <b>ИНН:</b> {data['inn']}\n"
        f"📌 <b>Номер:</b> {data.get('number', 'Не указан')}\n"
        f"📌 <b>Профиль Wildberries:</b> {data['marketplace_link']}\n\n"
        f"📊 <b>Данные Wildberries:</b>\n"
        f"⭐ Оценка: {wildberries_data.get('valuation', 'Нет данных')}\n"
        f"💬 Отзывы: {wildberries_data.get('feedbacks_count', 'Нет данных')}\n"
        f"📦 Продажи: {wildberries_data.get('sale_quantity', 'Нет данных')}\n"        
        f"🛑 Недобросовестный блок: {checko_data.get('Недобросовестный блок', 'Нет данных')}\n"
        f"👨‍💼 Массовый руководитель: {checko_data.get('Массовый руководитель', 'Нет данных')}\n"
        f"🏢 Массовый учредитель: {checko_data.get('Массовый учредитель', 'Нет данных')}\n"
        f"⚠️ Санкции: {checko_data.get('Санкции', 'Нет данных')}\n"
        f"📦 Раздел товаров: {excel_data.get('Раздел товаров', 'Нет данных')}\n"
        f"🛍️ Категория товаров: {excel_data.get('Категория товаров', 'Нет данных')}",
        parse_mode="HTML"
    )

    # **Создаем объект анализа рисков**
    risk_analysis = RiskAnalysis()
    risk_analysis.analyze({
        "valuation": wildberries_data.get("valuation"),
        "feedbacks_count": wildberries_data.get("feedbacks_count"),
        "sale_quantity": wildberries_data.get("sale_quantity"),
        "mass_rukovod": checko_data.get("mass_rukovod"),
        "sanctions": checko_data.get("sanctions"),
        "category": excel_data.get("Категория товаров")
    })

    # **Получаем результаты анализа**
    risks = risk_analysis.get_results()

    await state.update_data(risks=json.dumps(risks))

    # **Формируем вывод с HTML-экранированием**
    def escape_html(text):
        return str(text).replace("<", "&lt;").replace(">", "&gt;")

    risk_summary = "\n".join(
        [f"🔴 {escape_html(r)}" for r in risks["high_risks"]] +
        [f"🟠 {escape_html(r)}" for r in risks["medium_risks"]] +
        [f"🟡 {escape_html(r)}" for r in risks["low_risks"]]
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💡 Получить консультацию", callback_data="consult_risks")]
        ]
    ) if any(risks.values()) else None

    await message.answer(
        f"📊 <b>Анализ рисков:</b>\n{risk_summary if risk_summary else 'Риски не выявлены'}",
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(lambda c: c.data == "consult_risks")
async def choose_risk_category(callback_query: CallbackQuery, state: FSMContext):
    """
    Позволяет пользователю выбрать категорию риска для получения консультации.
    """
    # Получаем сохранённые риски из state
    data = await state.get_data()
    risks = json.loads(data.get("risks", "{}"))  

    risk_counts = {
        "high": len(risks.get("high_risks", [])),
        "medium": len(risks.get("medium_risks", [])),
        "low": len(risks.get("low_risks", []))
    }

    if all(count == 0 for count in risk_counts.values()):
        await callback_query.message.answer("✅ У вас нет выявленных рисков.")
        return

    # Создаём кнопки только для тех категорий, где есть риски
    keyboard_buttons = []
    if risk_counts["high"] > 0:
        keyboard_buttons.append([InlineKeyboardButton(text=f"🔴 Высокий ({risk_counts['high']})", callback_data="risk_category_high")])
    if risk_counts["medium"] > 0:
        keyboard_buttons.append([InlineKeyboardButton(text=f"🟠 Средний ({risk_counts['medium']})", callback_data="risk_category_medium")])
    if risk_counts["low"] > 0:
        keyboard_buttons.append([InlineKeyboardButton(text=f"🟡 Низкий ({risk_counts['low']})", callback_data="risk_category_low")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback_query.message.answer(
        "📌 Выберите категорию риска, по которой хотите получить консультацию:",
        reply_markup=keyboard
    )
    await callback_query.answer()



@router.callback_query(lambda c: c.data.startswith("risk_category_"))
async def choose_specific_risk(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Показывает пользователю конкретные риски в выбранной категории.
    """
    category = callback_query.data.split("_")[-1]  # Получаем категорию риска (high, medium, low)

    # 🔥 Исправление: Загружаем данные и конвертируем JSON-строку обратно в словарь
    data = await state.get_data()
    risks = data.get("risks", "{}")  # Если нет рисков, подставляем пустой JSON

    if isinstance(risks, str):  # Если строка, преобразуем обратно
        try:
            risks = json.loads(risks)
        except json.JSONDecodeError:
            risks = {}

    # 🔍 Отладка
    print(f"📊 Риски в категории {category}: {risks}")

    risk_list = risks.get(f"{category}_risks", [])

    if not risk_list:
        await callback_query.message.answer("❌ В данной категории рисков нет.")
        return

    # 🔥 Исправление: поменяли `_` на `:` в callback_data
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=risk, callback_data=f"fix_risk:{risk}")] for risk in risk_list
        ]
    )

    await callback_query.message.answer(
        f"Выберите конкретный риск в категории {'🔴 Высокий' if category == 'high' else '🟠 Средний' if category == 'medium' else '🟡 Низкий'} для консультации:",
        reply_markup=keyboard
    )
    await callback_query.answer()




import re
from html import escape

@router.callback_query(lambda c: c.data.startswith("fix_risk:"))
async def fix_specific_risk(callback_query: types.CallbackQuery):
    """
    Отправляет конкретный риск в Yandex GPT и получает рекомендации.
    """
    risk_name = callback_query.data.split("fix_risk:")[-1]
    print(f"🛠 Выбранный риск: {risk_name}")  

    # Запрашиваем советы у Yandex GPT
    gpt_response = await query_yandex_gpt(risk_name)

    # 🔥 Преобразуем `**жирный текст**` в `<b>жирный текст</b>`
    formatted_gpt_response = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", gpt_response)

    # Удаляем все лишние звездочки `*`
    formatted_gpt_response = formatted_gpt_response.replace("*", "")

    # Экранируем опасные символы, но оставляем HTML-теги `<b>...</b>`
    formatted_gpt_response = escape(formatted_gpt_response, quote=False)

    # Убираем экранирование тегов `<b>...</b>` после `escape()`
    formatted_gpt_response = formatted_gpt_response.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")

    print(f"✅ Отправляемое сообщение:\n{formatted_gpt_response}")  # Проверяем перед отправкой

    # 🚀 Отправляем сообщение
    await callback_query.message.answer(
        f"📌 <b>Консультация по риску:</b> <b>{escape(risk_name)}</b>\n\n"
        f"{formatted_gpt_response}",
        parse_mode="HTML"
    )
    await callback_query.answer()



async def query_yandex_gpt(marker_name: str) -> str:
    print(f"🔍 Отправляем в GPT: {marker_name}")  # 🔥 Логируем запрос

    prompt = {
        "modelUri": "gpt://b1gtrijf1l4e7qqg3o8m/yandexgpt-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": "2000"
        },
        "messages": [
            {
                "role": "system",
                "text": "Ты финансовый консультант.\
                К тебе пришел клиент с причиной низкой скоринговой оценки.\
                Предложи ему пути решения проблемы для повышения скоринговой оценки.\
                Не грузи клиента, дай максимум 3 совета."
            },
            {
                "role": "user",
                "text": marker_name
            }
        ]
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Api-Key AQVNzpC6YgzXzixqHMjlWioapUB9MSNhgD5xv9Br"
    }

    response = requests.post(url, headers=headers, json=prompt)

    if response.status_code == 200:
        gpt_text = response.json()['result']['alternatives'][0]['message']['text']
        print(f"✅ GPT ответ: {gpt_text}")  # 🔍 Логируем ответ от GPT
        return gpt_text
    else:
        error_msg = f"Ошибка: {response.status_code}, {response.text}"
        print(f"❌ GPT ошибка: {error_msg}")  # 🔥 Логируем ошибку
        return error_msg