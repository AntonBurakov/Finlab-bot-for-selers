import re
import requests
from collections import Counter

# Ключевые слова по категориям (расширенная версия)
category_keywords = {
    'Обувь': [
        'обувь', 'ботинки', 'туфли', 'кроссовки', 'сандалии', 'сабо', 'сланцы', 'тапки', 'угги', 'валенки',
        'лоферы', 'мокасины', 'шлёпки', 'дерби', 'берцы', 'эспадрильи', 'балетки', 'ботильоны', 'сникерсы',
        'слипоны', 'челси', 'резиновые сапоги', 'босоножки', 'тапочки', 'домашняя обувь', 'мюли', 'вьетнамки'
    ],
    'Одежда': [
        'одежда', 'платье', 'футболка', 'брюки', 'куртка', 'юбка', 'пальто', 'штаны', 'джинсы', 'кофта',
        'свитшот', 'толстовка', 'сорочка', 'жилет', 'комбинезон', 'худи', 'блузка', 'реглан', 'майка',
        'жакет', 'костюм', 'пуховик', 'плащ', 'ветровка', 'тренч', 'шорты', 'боди', 'пижама', 'домашний комплект',
        'рубашка', 'кардиган', 'леггинсы', 'топ', 'лонгслив', 'комплект', 'ночнушка', 'термобелье'
    ],
    'Товары для детей': [
        'дет', 'детский', 'игрушк', 'малыш', 'памперс', 'ребенок', 'дошкольн', 'кукла', 'конструктор', 'погремушка',
        'развивающ', 'ползунки', 'коляска', 'подгузник', 'манеж', 'ходунки', 'горшок', 'развивающая игрушка', 'костюм детский'
    ],
    'Животные': [
        'животн', 'кошк', 'собак', 'корм', 'зоотовар', 'наполнитель', 'миска', 'переноска', 'намордник',
        'ошейник', 'лежак', 'будка', 'когтеточка', 'шлейка', 'игрушка для животных', 'лапомойка', 'поилка'
    ],
    'Электроника и техника': [
        'электроника', 'техника', 'смартфон', 'телефон', 'планшет', 'наушник', 'телевизор', 'пауэрбанк',
        'зарядка', 'мышь', 'клавиатура', 'ноутбук', 'монитор', 'колонка', 'пылесос', 'миксер', 'блендер',
        'холодильник', 'утюг', 'фен', 'микроволновка', 'камера', 'веб-камера', 'кулер', 'приставка', 'часы умные',
        'фитнес-браслет', 'электробритва', 'гаджет', 'геймпад'
    ],
    'Автомобили и транспорт': [
        'авто', 'автомобиль', 'транспорт', 'шина', 'дворник', 'масло', 'автоаксессуар', 'лампа', 'автокресло',
        'домкрат', 'автотовар', 'коврик', 'полироль', 'насадка', 'диагностика', 'компрессор', 'регистратор',
        'держатель', 'зарядка в авто', 'ковры', 'щётка', 'аптечка', 'огнетушитель'
    ],
    'Мебель': [
        'мебель', 'диван', 'кровать', 'стул', 'стол', 'шкаф', 'пуфик', 'комод', 'кресло', 'тумба',
        'обеденный', 'гарнитур', 'матрас', 'кухонный', 'полка', 'стеллаж', 'пеленальный', 'раскладушка',
        'угловой диван', 'барный стул', 'журнальный столик', 'модульная мебель'
    ],
    'Товары для дома': [
        'дом', 'подушка', 'плед', 'штора', 'постель', 'ковер', 'скатерть', 'полотенце', 'органайзер',
        'корзина', 'посуда', 'занавеска', 'чехол', 'покрывало', 'коврик', 'наволочка', 'салфетка',
        'держатель', 'губка', 'ящик', 'вешалка', 'совок', 'тряпка', 'контейнер', 'ящик для хранения'
    ],
    'Аксессуары и ювелирка': [
        'аксессуар', 'украшен', 'серьг', 'кольц', 'браслет', 'ювелир', 'часы', 'подвеска', 'бижутерия',
        'зажим', 'ремень', 'обруч', 'колье', 'диадема', 'булавка', 'запонка', 'шарф', 'галстук', 'брошь', 'заколка'
    ],
    'Спорт и активный отдых': [
        'спорт', 'тренажер', 'туризм', 'рыбалка', 'велосипед', 'груша', 'гантель', 'эспандер',
        'лыжи', 'самокат', 'теннис', 'мяч', 'ролики', 'батут', 'скакалка', 'тренажёр', 'экипировка',
        'коврик', 'спортивная бутылка', 'рюкзак для спорта'
    ],
    'Стройка и ремонт': [
        'строит', 'ремонт', 'шуруп', 'дюбель', 'инструмент', 'дрель', 'перфоратор', 'отвёртка',
        'краска', 'гвоздь', 'рулетка', 'уровень', 'шпатель', 'пена', 'клей', 'замазка', 'изоляция',
        'сверло', 'грунтовка', 'болт', 'профиль', 'плиткорез', 'лестница', 'стяжка'
    ],
    'Канцтовары и книги': [
        'канц', 'книга', 'тетрадь', 'ручка', 'карандаш', 'маркер', 'альбом', 'фломастер', 'бумага',
        'ежедневник', 'блокнот', 'папка', 'скрепка', 'линейка', 'клей канцелярский', 'степлер', 'набор'
    ],
}

headers = {"User-Agent": "Mozilla/5.0"}

# --- Функции для загрузки и категоризации по названию ---
def fetch_all_product_names(seller_id: int, max_pages=50) -> list:
    all_names = []
    for page in range(1, max_pages + 1):
        url = f"https://catalog.wb.ru/sellers/catalog?appType=1&curr=rub&dest=-1257786&page={page}&sort=popular&spp=30&supplier={seller_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break
        try:
            data = response.json()
            products = data.get("data", {}).get("products", [])
        except Exception:
            break
        if not products:
            break
        for product in products:
            name = product.get("name", "")
            all_names.append(name)
    return all_names

def map_name_to_category(name: str) -> str:
    name = name.lower()
    for category, keywords in category_keywords.items():
        for kw in keywords:
            if kw in name:
                return category
    return "Другое"

def analyze_categories_by_name(names: list) -> Counter:
    category_counts = Counter()
    for name in names:
        category = map_name_to_category(name)
        category_counts[category] += 1
    return category_counts

# Простая имитация цветовой категоризации по количеству повторов
def categorize_risks_by_frequency(counter):
    high = [cat for cat, count in counter.items() if count >= 10]
    medium = [cat for cat, count in counter.items() if 5 <= count < 10]
    low = [cat for cat, count in counter.items() if count < 5]
    return {
        "high_risks": high,
        "medium_risks": medium,
        "low_risks": low
    }

def run_wb_scoring(seller_id: int) -> dict:
    all_cards = []
    page = 1

    while True:
        url = f"https://card.wb.ru/sellers/catalog?spp=30&regions=80,38,4,115,83,33,70,82,86,75,30,40,1,66,110,31,22,48,71,114&dest=-1257786&page={page}&supplier={seller_id}"
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise ValueError("Ошибка запроса данных WB")

        try:
            page_cards = response.json()["data"]["products"]
        except Exception:
            raise ValueError("Не удалось распарсить карточки WB")

        if not page_cards:
            break

        all_cards.extend(page_cards)
        page += 1

    if not all_cards:
        return {"score": 0.0, "risks": {}, "details": "Нет карточек"}

    cards = all_cards

    # Собираем текст заголовков
    title_text = " ".join(card.get("name", "") for card in cards).lower()

    # Подсчёт ключевых слов по категориям
    keyword_counter = Counter()
    for category, keywords in category_keywords.items():
        for word in keywords:
            keyword_counter[category] += len(re.findall(rf"\b{re.escape(word)}\b", title_text))

    # Считаем дополнительные параметры
    total_rating = 0
    total_feedbacks = 0
    total_items = 0
    total_price = 0

    for card in cards:
        rating = card.get("rating", 0)
        feedbacks = card.get("feedbacks", 0)
        priceU = card.get("priceU", 0) / 100  # Цена в рублях

        if feedbacks > 0:
            total_rating += rating * feedbacks
            total_feedbacks += feedbacks
        total_items += 1
        total_price += priceU

    avg_rating = round(total_rating / total_feedbacks, 2) if total_feedbacks else 0
    avg_price = round(total_price / total_items, 2) if total_items else 0

    # Категоризация рисков
    risk_groups = categorize_risks_by_frequency(keyword_counter)

    # Расчёт итогового score
    base_score = 1.0
    if risk_groups["high_risks"]:
        base_score -= 0.4
    if risk_groups["medium_risks"]:
        base_score -= 0.2
    if avg_rating < 3.5:
        base_score -= 0.2
    if total_feedbacks < 10:
        base_score -= 0.1

    final_score = max(0.0, round(base_score, 2))

    # Анализ продуктового микса
    product_names = [card.get("name", "") for card in cards]
    product_mix = analyze_categories_by_name(product_names)

    return {
        "score": final_score,
        "risks": risk_groups,
        "avg_rating": avg_rating,
        "avg_price": avg_price,
        "feedbacks": total_feedbacks,
        "cards_count": total_items,
        "product_mix": dict(product_mix)
    }