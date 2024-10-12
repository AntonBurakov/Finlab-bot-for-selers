from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

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
    await message.answer('Добро пожаловать в finalb помомшник!\nЯ умею:\n/register - помощь в подборе финансового продукта\n/assistent - виртуальный финансовый асистент, который поможет в ответе на вопросы\n/scoring - проведение скоринга')


@router.message(Command('assistent'))
async def help_command(message: Message):
    await message.answer('Я виртуальный финансовый аситсент! Чем я могу вам помочь')

@router.message(Command('scoring'))
async def register_command(message: Message, state: FSMContext):
    await state.set_state(Scoring.name)
    await message.answer('Для скоринговой оценки понадобится следующая информация: ФИО, номер телфона, ИНН.\n\nВведите ваше ФИО')

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
async def register_name(message: Message, state: FSMContext):
     await state.update_data(inn=message.text)
     data = await state.get_data()
     url = f'https://focus-api.kontur.ru/api3/scoring?inn={data["inn"]}&key=DEMO493156a753c0d86fb24c130fae824427c93a'
     response = requests.get(url)
     responseData = response.json()
     rating = responseData[0]['scoringData'][0]['rating']

     if 0 <= rating <= 39:
        emoji = "🔴"  # Красный круг для рейтинга 0-39
     elif 40 <= rating <= 69:
        emoji = "🟡"  # Желтый круг для рейтинга 40-69
     elif 70 <= rating <= 100:
        emoji = "🟢"  # Зеленый круг для рейтинга 70-100
     else:
        emoji = "❓"  # На случай, если значение рейтинга выходит за пределы

     await message.answer(f'Ваше имя: {data["name"]}\nВаш инн: {data["inn"]}\nНомер: {data["number"]}\nВаш скоринговый рейтинг: {rating} {emoji}')
     await state.clear()

