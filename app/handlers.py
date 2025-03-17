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

    # **Формируем вывод с HTML-экранированием**
    def escape_html(text):
        return str(text).replace("<", "&lt;").replace(">", "&gt;")

    risk_summary = "\n".join(
        [f"🔴 {escape_html(r)}" for r in risks["high_risks"]] +
        [f"🟠 {escape_html(r)}" for r in risks["medium_risks"]] +
        [f"🟡 {escape_html(r)}" for r in risks["low_risks"]]
    )

    # **Отправляем пользователю анализ рисков**
    print(f"Отправляемое сообщение:\n{risk_summary}")  # Отладочный вывод перед отправкой

    await message.answer(
        f"📊 <b>Анализ рисков:</b>\n{risk_summary if risk_summary else 'Риски не выявлены'}",
        parse_mode="HTML"
    )

    # **Завершаем FSM и очищаем состояние**
    await state.clear()






@router.callback_query(lambda c: c.data == 'show_reasons')
async def show_reasons(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer() 

    mock_response_data = [
        {
            "inn": "1234567890",
            "ogrn": "1234567890123",
            "focusHref": "https://focus.kontur.ru/card/1234567890",
            "scoringData": [
                {
                    "modelId": "model_1",
                    "modelName": "Standard Scoring Model",
                    "modelUpdateDate": "2024-01-01",
                    "rating": 39, 
                    "ratingLevel": "High",
                    "triggeredMarkers": [
                        {
                            "markerId": "marker_1",
                            "impact": "Reliability",
                            "weight": "Moderate",
                            "name": "Отсутствие уставного капитала",
                            "description": "Отсутствие уставного капитала."
                        },
                        {
                            "markerId": "marker_2",
                            "impact": "Reliability",
                            "weight": "Moderate",
                            "name": "Задолженности",
                            "description": "Задолженности на сумму 450 000 рублей."
                        }
                    ]
                }
            ]
        }
    ]

    markers = mock_response_data[0]['scoringData'][0]['triggeredMarkers']

    for marker in markers:
        await callback_query.message.answer(
            f'Причина: {marker["name"]}\n'
            f'Описание: {marker["description"]}\n'
            f'Хотите узнать, как это можно устранить?'
        )

        await callback_query.message.answer(
            'Нажмите на кнопку, чтобы узнать, как это исправить.',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Узнать', callback_data=f'fix_{marker["name"]}')]
            ])
        )

# Обработчик нажатия на кнопку с предложением узнать, как исправить проблему
@router.callback_query(lambda c: c.data.startswith('fix_'))
async def fix_marker(callback_query: CallbackQuery):
    # Извлекаем имя маркера из данных кнопки
    marker_name = callback_query.data[4:]  # Убираем 'fix_' из начала строки

    # Запрашиваем информацию у Yandex GPT о том, как исправить проблему
    gpt_response = await query_yandex_gpt(marker_name)

    # Отправляем ответ пользователю
    await callback_query.message.answer(
        f"<b>Информация о том, как устранить проблему:</b> <b>{marker_name}</b>\n\n{gpt_response}",
        parse_mode="HTML"
    )

async def query_yandex_gpt(marker_name: str) -> str:
    # Выполнение запроса к Yandex GPT
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
                Не грузи клиента, дай максимум 3 совета"
            },
            {
                "role": "user",
                "text": "{marker_name}"
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
        return response.json()['result']['alternatives'][0]['message']['text']
    else:
        return f"Ошибка: {response.status_code}, {response.text}"