from app.scoring_utils.checko_core import RiskAnalyzer
from app.scoring_utils.checko_core import run_checko_scoring
from app.scoring_utils.wb_core_full_from_notebook import run_wb_scoring_advanced
from aiogram import F, Router, types
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from unittest.mock import patch

import app.database.requests as rq
from app.scoring_utils.wildberries import fetch_wildberries_data
from app.scoring_utils.historical_csv import get_seller_data_from_csv
from app.scoring_utils.scoring_risks import RiskAnalysis
import requests
import json
import random  
import re
import html 
from html import escape

router = Router()

# 🔥 ИЗМЕНЕНИЕ: Явный API-ключ Yandex GPT (временно)
YANDEX_GPT_API_KEY = "AQVNzpC6YgzXzixqHMjlWioapUB9MSNhgD5xv9Br"  # ← Вставьте свой API-ключ здесь

class Scoring(StatesGroup):
    name = State()
    number = State()
    inn = State()
    loan_amount = State()
    marketplace_link = State()

### 📌 1. Запрос согласия перед регистрацией
@router.message(CommandStart())
async def start_command(message: Message):
    print(f"Получено сообщение: {message.text} от {message.from_user.id}")
    consent_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да, согласен", callback_data="consent_granted")]
        ]
    )

    await message.answer(
        "👋 <b>Добро пожаловать в Payrix bot!</b>\n\n"
        "Я создан, чтобы <b>помогать селлерам маркетплейсов</b> в поиске подходящего финансирования 💰 и в улучшении финансовой устойчивости бизнеса 📈.\n\n"
        "🛠️ <b>Что я умею:</b>\n"
        "• Подобрать <b>финансовые предложения</b>, соответствующие вашему бизнес-профилю;\n"
        "• Провести <b>скоринговую оценку</b> по ИНН, продажам и данным Wildberries;\n"
        "• <b>Выявить риски</b>, которые могут помешать получению финансирования;\n"
        "• Предложить <b>персональные советы</b> от виртуального финансового консультанта 🤖 (на базе YandexGPT).\n\n"
        "💡 <b>Как начать:</b>\n"
        "Всё просто — нужно ввести основную информацию о себе: ФИО, номер телефона, ИНН и ссылку на профиль продавца на маркетплейсе.\n"
        "После этого я покажу, какие программы вам подходят и как можно улучшить ваши шансы на одобрение.\n\n"
        "🚀 <b>Готовы?</b> Давайте начнём — сначала подтвердите согласие на обработку персональных данных 👇",
        parse_mode="HTML",
        reply_markup=consent_markup
    )

@router.callback_query(lambda c: c.data == "consent_granted")
async def process_consent(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    # Записываем ID в БД ТОЛЬКО ПОСЛЕ СОГЛАСИЯ
    await rq.set_user(user_id)
    await rq.update_data_permission(user_id, True)  # Фиксируем согласие
    
    await callback_query.message.edit_text(
        "✅ <b>Спасибо за согласие!</b> Теперь вы можете пользоваться ботом.\n\n"
        "📌 Доступные команды:\n"
        "  • <b>/scoring</b> — Запуск скоринга\n"
        "  • <b>/revoke_consent</b> — Отозвать согласие и удалить данные",
        parse_mode="HTML"
    )
    await callback_query.answer()


### 📌 2. Обработчик отзыва согласия и удаления данных
@router.message(Command("revoke_consent"))
async def revoke_consent_handler(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑️ Да, удалить данные", callback_data="confirm_revoke")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_revoke")]
        ]
    )
    
    await message.answer(
        "⚠️ <b>Вы уверены, что хотите удалить все ваши данные?</b>\n"
        "Это действие необратимо!", parse_mode="HTML", reply_markup=keyboard
    )

@router.callback_query(lambda c: c.data in ["confirm_revoke", "cancel_revoke"])
async def process_revoke(callback_query: CallbackQuery):
    if callback_query.data == "confirm_revoke":
        await rq.delete_user(callback_query.from_user.id)
        await callback_query.message.edit_text("✅ Ваши данные успешно удалены.")
    else:
        await callback_query.message.edit_text("❌ Удаление отменено.")

    await callback_query.answer()


### 📌 3. Запрос скоринга только если есть согласие
@router.message(Command('scoring'))
async def register_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await rq.get_user(user_id)

    # Проверяем, есть ли пользователь и дал ли он согласие
    if not user or not user.data_permission:
        await message.answer("❌ Вы не дали согласие на обработку персональных данных. Введите /start, чтобы продолжить.")
        return

    # Начинаем сбор данных (ФИО)
    await state.set_state(Scoring.name)
    await message.answer("✍️ <b>Введите ваше ФИО</b>", parse_mode="HTML")


### 📌 4. Сбор данных (ФИО, телефон, ИНН)
@router.message(Scoring.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Scoring.number)
    await message.answer("📞 <b>Введите ваш номер телефона</b>", parse_mode="HTML")

@router.message(Scoring.number)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.text)
    await state.set_state(Scoring.inn)
    await message.answer("🔢 <b>Введите ваш ИНН</b>", parse_mode="HTML")



@router.message(Scoring.inn)
async def register_inn(message: Message, state: FSMContext):
    await state.update_data(inn=message.text)
    await state.set_state(Scoring.loan_amount)
    await message.answer("💰 <b>Какую сумму займа вы хотите получить (в рублях)?</b>", parse_mode="HTML")


# Новый хендлер для суммы займа
@router.message(Scoring.loan_amount)
async def register_loan_amount(message: Message, state: FSMContext):
    try:
        loan_amount = float(message.text.replace(" ", "").replace(",", ""))
        if loan_amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите корректную сумму займа (например, 1000000):")
        return

    await state.update_data(loan_amount=loan_amount)
    await state.set_state(Scoring.marketplace_link)
    await message.answer("🔗 <b>Введите ссылку на ваш профиль в маркетплейсе</b>", parse_mode="HTML")


@router.message(Scoring.marketplace_link)
async def register_marketplace_link(message: Message, state: FSMContext):
    await state.update_data(marketplace_link=message.text)
    data = await state.get_data()

    # Получаем seller_id из ссылки
    seller_id_match = re.search(r"/seller/(\d+)", data["marketplace_link"])
    if not seller_id_match:
        await message.answer("Ошибка: Не удалось извлечь seller_id из ссылки.")
        return
    seller_id = int(seller_id_match.group(1))

    # 1. Checko scoring
    try:
        checko_score_data = run_checko_scoring(data["inn"], loan_amount=data.get("loan_amount", 0))
        checko_score = round(checko_score_data["score"] * 100)
    except Exception as e:
        await message.answer(f"❌ Ошибка при получении скоринга Checko: {e}")
        return

    # 2. CSV scoring
    try:
        csv_data = get_seller_data_from_csv("Истор данные.csv", data["marketplace_link"])
        # csv_data["score"] is в десятых долях процента, например, 619 → 61.9
        try:
            csv_score = round(float(csv_data.get("score", 0)) / 10)
        except Exception:
            csv_score = 0
    except Exception as e:
        await message.answer(f"❌ Ошибка при анализе истории продаж: {e}")
        return

    # 3. WB advanced scoring
    try:
        wb_result = run_wb_scoring_advanced(seller_id)
        wb_score = wb_result["score"]
    except Exception as e:
        await message.answer(f"❌ Ошибка при анализе Wildberries: {e}")
        return

    # Собираем все риски
    risks = {
        "high_risks": [],
        "medium_risks": [],
        "low_risks": []
    }
    # Checko
    if "risks" in checko_score_data:
        risks["high_risks"].extend(checko_score_data["risks"].get("high_risks", []))
        risks["medium_risks"].extend(checko_score_data["risks"].get("medium_risks", []))
        risks["low_risks"].extend(checko_score_data["risks"].get("low_risks", []))
    # CSV
    if csv_data.get("csv_high_risks"):
        risks["high_risks"].extend(csv_data["csv_high_risks"])
    if csv_data.get("csv_medium_risks"):
        risks["medium_risks"].extend(csv_data["csv_medium_risks"])
    if csv_data.get("csv_low_risks"):
        risks["low_risks"].extend(csv_data["csv_low_risks"])
    # WB
    if wb_result.get("risks"):
        risks["high_risks"].extend(wb_result["risks"].get("high_risks", []))
        risks["medium_risks"].extend(wb_result["risks"].get("medium_risks", []))
        risks["low_risks"].extend(wb_result["risks"].get("low_risks", []))

    # Удаляем маркеры "Умеренный риск:" и "Высокий риск:" из текста рисков и делаем первую букву заглавной
    def clean_risk_label(text):
        cleaned = text.replace("Умеренный риск: ", "").replace("Высокий риск: ", "")
        return cleaned[:1].upper() + cleaned[1:] if cleaned else ""

    for category in ["high_risks", "medium_risks", "low_risks"]:
        risks[category] = [clean_risk_label(r) for r in risks.get(category, [])]

    # Сохраняем риски в state
    await state.update_data(risks=json.dumps(risks))

    # Финальный скор-балл
    final_score = round(checko_score * 0.2 + csv_score * 0.4 + wb_score * 0.4)

    # Новый текстовый результат
    summary_text = (
        f"✅ <b>Скоринг завершён!</b>\n\n"
        f"• <b>Checko:</b> {checko_score}/100\n"
        f"• <b>История продаж:</b> {csv_score}/100\n"
        f"• <b>Wildberries:</b> {wb_score}/100\n"
        f"────────────────────────────\n"
        f"🏁 <b>Итоговый скор-балл:</b> <b>{final_score}/100</b>\n"
        f"{(
            '🎯 <b>На основе вашей оценки вам могут подойти следующие продукты:</b>\n'
            '🔷 <a href=\"https://finlab.ru/credits/alfa/kredit-dlya-biznesa\">Кредит для бизнеса (Альфа-Банк)</a>\n'
            '🔷 <a href=\"https://finlab.ru/credits/promsvyaz/bsb-credit-bez-bumag-oborot-a\">Кредит Без бумаг | На развитие (Промсвязьбанк)</a>\n'
            '🔷 <a href=\"https://finlab.ru/credits/sber/credits-sber-kredit-oborotnyu\">Кредит для бизнеса (Сбербанк)</a>\n'
            '🔷 <a href=\"https://finlab.ru/credits/fordewind/credits-fordewind-kreditovanie-ot-mfk-fordevind\">Кредитование от МФК Фордевинд (МФК Фордевинд)</a>'
        ) if final_score >= 60 else 'ℹ️ Для вас доступна консультация по рискам.'}\n"
        f"📂 Нажмите кнопку ниже, чтобы увидеть выявленные риски."
    )

    # Новые кнопки
    buttons = [[InlineKeyboardButton(text="📂 Показать риски", callback_data="show_risk_categories")]]
    reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    await message.answer(
        summary_text,
        parse_mode="HTML",
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )


    @router.callback_query(lambda c: c.data == "show_risk_categories")
    async def show_risk_categories(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        risks = json.loads(data.get("risks", "{}"))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🔴 Высокие риски ({len(risks.get('high_risks', []))})", callback_data="expand|high")],
            [InlineKeyboardButton(text=f"🟠 Умеренные риски ({len(risks.get('medium_risks', []))})", callback_data="expand|medium")],
            [InlineKeyboardButton(text=f"🟡 Низкие риски ({len(risks.get('low_risks', []))})", callback_data="expand|low")]
        ])

        await callback.message.answer("📂 <b>Выберите группу рисков:</b>", reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()

    @router.callback_query(lambda c: c.data.startswith("expand|"))
    async def expand_risk_group(callback: CallbackQuery, state: FSMContext):
        data = await state.get_data()
        risks = json.loads(data.get("risks", "{}"))
        _, category = callback.data.split("|")

        category_map = {
            "high": ("🔴 Высокие риски", risks.get("high_risks", [])),
            "medium": ("🟠 Умеренные риски", risks.get("medium_risks", [])),
            "low": ("🟡 Низкие риски", risks.get("low_risks", [])),
        }

        title, items = category_map.get(category, ("Неизвестно", []))

        if not items:
            await callback.message.answer(f"❌ В категории <b>{title}</b> нет рисков.", parse_mode="HTML")
        else:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=item, callback_data=f"fix_risk|{category}|{i}")]
                    for i, item in enumerate(items)
                ]
            )
            await callback.message.answer(
                text=f"<b>{title}</b>\n\nНажмите на интересующий риск, чтобы получить консультацию:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )

        await callback.answer()


@router.callback_query(lambda c: c.data.startswith("fix_risk|"))
async def fix_specific_risk(callback_query: types.CallbackQuery, state: FSMContext):
    #Отправляет конкретный риск в Yandex GPT и получает рекомендации.
    try:
        _, category, risk_index = callback_query.data.split("|")  
        risk_index = int(risk_index)
    except ValueError:
        await callback_query.message.answer("❌ Ошибка: неверный формат данных.")
        return

    # Загружаем риски из state
    data = await state.get_data()
    risks = json.loads(data.get("risks", "{}"))
    
    category_key = f"{category}_risks"
    risk_list = risks.get(category_key, [])

    if risk_index >= len(risk_list):
        await callback_query.message.answer("❌ Ошибка: риск не найден.")
        return

    risk_name = risk_list[risk_index]

    # 🔥 Получаем ответ от Yandex GPT
    gpt_response = await query_yandex_gpt(risk_name)

    # **ОЧИСТКА ТЕКСТА ОТ ОШИБОК**
    gpt_response = escape(gpt_response, quote=False)  # Экранируем HTML
    gpt_response = gpt_response.replace("&lt;b&gt;", "<b>").replace("&lt;/b&gt;", "</b>")  # Восстанавливаем теги
    gpt_response = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", gpt_response)  # **жирный** → <b>жирный</b>
    gpt_response = gpt_response.replace("*", "")  # Убираем звездочки

    await callback_query.message.answer(
        f"📌 <b>Консультация по риску:</b> <b>{escape(risk_name)}</b>\n\n"
        f"{gpt_response}",
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
        "Authorization": "Api-Key AQVN2GpddcPYIqY3gnlQOZob7memzv-BKsPg7DIF"
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

