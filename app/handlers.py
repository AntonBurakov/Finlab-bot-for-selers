from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from unittest.mock import patch
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import app.keyboards as kb
import app.database.requests as rq
import requests
import json

router = Router()

class Scoring(StatesGroup):
    name = State()
    number = State()
    inn = State()
    

@router.message(CommandStart())
async def start_command(message: Message):
    await rq.set_user(message.from_user.id)
    await message.answer('Добро пожаловать в finalb помомшник!\nЯ умею:\n/scoring - проведение скоринга')


@router.message(Command('assistent'))
async def help_command(message: Message):
    await message.answer('Я виртуальный финансовый аситсент! Чем я могу вам помочь')

@router.message(Command('scoring'))
async def register_command(message: Message, state: FSMContext):
    consent_markup = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Да, согласен', callback_data='yes')]])

    # Отправляем сообщение с кнопкой
    await message.answer('Для скоринговой оценки понадобится следующее разрешение: согласны ли вы на обработку персональных данных?', reply_markup=consent_markup)

@router.callback_query(lambda c: c.data == 'yes')
async def process_consent(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.answer()  # Закрываем всплывающее окно
    user_id = callback_query.from_user.id
    # Записываем согласие в базу данных
    await rq.update_data_permission(user_id, True)  # Установите permission в True

    await state.set_state(Scoring.name)
    await callback_query.message.answer('Спасибо за согласие! Теперь введите ваше ФИО')


@router.message(Scoring.name)
async def register_name(message: Message, state: FSMContext):
     await state.update_data(name=message.text)
     await state.set_state(Scoring.number)
     await message.answer('Введите ваш номер телефона')

@router.message(Scoring.number)
async def register_number(message: Message, state: FSMContext):
     await state.update_data(number=message.text)
     await state.set_state(Scoring.inn)
     await message.answer('Введите ваш инн')

@router.message(Scoring.inn)
async def register_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text)
    data = await state.get_data()

    await rq.update_user_data(
        tg_id=message.from_user.id, 
        name=data.get("name"),  # Имя
        phone_number=data.get("number"),  # Номер телефона
        inn=data["inn"]  # ИНН
    )
    
    url = f'https://focus-api.kontur.ru/api3/scoring?inn={data["inn"]}&key=DEMO493156a753c0d86fb24c130fae824427c93a'

    # Пример ответа от API
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

    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response_data
        response = requests.get(url)
        responseData = response.json()

        # Получаем рейтинг из замоканного ответа
        rating = responseData[0]['scoringData'][0]['rating']
        markers = responseData[0]['scoringData'][0]['triggeredMarkers']

        # Определяем эмодзи на основе рейтинга
        if 0 <= rating <= 39:
            emoji = "🔴"
        elif 40 <= rating <= 69:
            emoji = "🟡"
        elif 70 <= rating <= 100:
            emoji = "🟢"
        else:
            emoji = "❓"

        await message.answer(
            f'Ваше имя: {data.get("name", "Не указано")}\n'
            f'Ваш инн: {data["inn"]}\n'
            f'Номер: {data.get("number", "Не указан")}\n'
            f'Ваш скоринговый рейтинг: {rating} {emoji}'
        )


        if markers:
            await message.answer(
                'Обнаружено несколько причин низкой скоринговой оценки. Хотите ли вы посмотреть на них?',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Да', callback_data='show_reasons')]
                ])
            )

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
        f"Информация о том, как устранить проблему '{marker_name}':\n{gpt_response}"
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
        "Authorization": "Api-Key AQVN2v80bFuxVQGnizZzIzeC6W3l8jZrvmjEIOTk"
    }

    response = requests.post(url, headers=headers, json=prompt)

    if response.status_code == 200:
        return response.json()['result']['alternatives'][0]['message']['text']
    else:
        return f"Ошибка: {response.status_code}, {response.text}"