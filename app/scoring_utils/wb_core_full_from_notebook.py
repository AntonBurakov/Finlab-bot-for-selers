import requests
from collections import Counter
import re

headers = {
    "User-Agent": "Mozilla/5.0"
}

# Ключевые слова по категориям
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
        'ошейник', 'лежак', 'будка', 'когтеточка', 'шлейка', 'игрушка для животных', 'будка', 'лапомойка', 'поилка'
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
    'Стройка': [
        'строит', 'ремонт', 'шуруп', 'дюбель', 'инструмент', 'дрель', 'перфоратор', 'отвёртка',
        'краска', 'гвоздь', 'рулетка', 'уровень', 'шпатель', 'пена', 'клей', 'замазка', 'изоляция',
        'сверло', 'грунтовка', 'болт', 'профиль', 'плиткорез', 'лестница', 'стяжка'
    ],
    'Канцтовары и книги': [
        'канц', 'книга', 'тетрадь', 'ручка', 'карандаш', 'маркер', 'альбом', 'фломастер', 'бумага',
        'ежедневник', 'блокнот', 'папка', 'скрепка', 'линейка', 'клей канцелярский', 'степлер',
        'набор для рисования', 'ручка гелевая', 'обложка', 'подставка для книг'
    ],
    'Хобби и развлечения': [
        'хобби', 'развлечен', 'игра', 'настолк', 'головоломка', 'модель', 'пазл', 'коллекция',
        'раскраска', 'квест', 'макияж', 'рисование', 'музыка', 'пластилин', 'лепка', 'вышивка',
        'вязание', 'конструктор для взрослых', 'фигурка', '3d-пазл'
    ],
    'Сад и садоводство': [
        'сад', 'огород', 'рассада', 'лопата', 'грабли', 'тачка', 'газон', 'полив', 'садовый', 'секатор',
        'удобрение', 'парник', 'горшок', 'саженец', 'рассадник', 'сажалка', 'плодовое дерево', 'капельный полив'
    ],
    'Красота и здоровье': [
        'косметик', 'крем', 'шампунь', 'маска', 'бальзам', 'гель', 'сыворотка', 'здоровье', 'уход',
        'витамин', 'маникюр', 'эпилятор', 'пилка', 'бьюти', 'аромат', 'зубная паста', 'щётка зубная',
        'дезодорант', 'лосьон', 'бальзам для губ', 'средство для умывания', 'гигиена'
    ],
    'Продукты и напитки': [
        'продукт', 'еда', 'напиток', 'чай', 'кофе', 'шоколад', 'печенье', 'крупа', 'макарон',
        'сладость', 'снек', 'вода', 'лимонад', 'соус', 'приправ', 'батончик', 'мёд', 'орехи',
        'масло растительное', 'консервы', 'злаки', 'сухофрукты'
    ],
    'Прочее': []
}


def map_name_to_category(name):
    name_lower = name.lower()
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if re.search(rf'\b{keyword}', name_lower):  # ищем начало слова
                return category
    return 'Прочее'

def fetch_all_product_names(seller_id, max_pages=10):
    all_names = []
    for page in range(1, max_pages + 1):
        url = f"https://catalog.wb.ru/sellers/catalog?appType=1&curr=rub&dest=-1257786&page={page}&sort=popular&spp=30&supplier={seller_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break

        data = response.json()
        products = data.get("data", {}).get("products", [])
        if not products:
            break

        for product in products:
            name = product.get("name", "")
            all_names.append(name)
    return all_names

def analyze_categories_by_name(names):
    category_counts = Counter()
    for name in names:
        category = map_name_to_category(name)
        category_counts[category] += 1
    return category_counts


def analyze_feedbacks_concentration(seller_id):
    all_feedbacks = []
    all_products = []
    page = 1

    while True:
        url = f"https://catalog.wb.ru/sellers/catalog?appType=1&curr=rub&dest=-1257786&page={page}&sort=popular&spp=30&supplier={seller_id}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            break

        data = response.json()
        products = data.get("data", {}).get("products", [])
        if not products:
            break  # закончились страницы

        for product in products:
            fb = product.get("feedbacks", 0)
            name = product.get("name", "")
            all_feedbacks.append(fb)
            all_products.append((name, fb))

        page += 1  # следующая страница

    if not all_feedbacks:
        # print("❓ Нет данных об отзывах.")
        return None, None, None, None

    total_feedbacks = sum(all_feedbacks)
    max_feedbacks = max(all_feedbacks)
    max_name = next(name for name, fb in all_products if fb == max_feedbacks)
    share = max_feedbacks / total_feedbacks * 100

    return max_name, max_feedbacks, total_feedbacks, share


# Оценка уровня товарной концентрации
# if num_categories == 1:
#     print("\n🔴 Обратите внимание: вся ваша продукция представлена в одной категории. Это повышает риск зависимости от колебаний спроса в данной нише. Рекомендуется рассмотреть возможность диверсификации ассортимента.")
# elif num_categories == 2:
#     print("\n🟡 Умеренный уровень концентрации: товары представлены в двух категориях. Это может ограничивать устойчивость бизнеса к рыночным изменениям. Подумайте о расширении номенклатуры.")
# else:
#     print("\n🟢 Ассортимент охватывает несколько категорий, что снижает риск концентрации и повышает устойчивость продаж.")

import requests
import json

def fetch_wb_raw_data(seller_id: str):
    url = f"https://suppliers-shipment-2.wildberries.ru/api/v1/suppliers/{seller_id}"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "ru-RU,ru;q=0.9",
        "origin": "https://www.wildberries.ru",
        "referer": f"https://www.wildberries.ru/seller/{seller_id}",
        "sec-ch-ua": '"Chromium";v="113", "Google Chrome";v="113", "Not-A.Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/113.0.0.0 Safari/537.36",
        "x-client-name": "site"
    }

    cookies = {
        "_wbauid": "4623112171727628664",
        "_cp": "1"
    }

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"❌ Ошибка запроса: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")


import pandas as pd

# Загрузка файла без заголовков
df = pd.read_excel('12.xlsx', header=None)

# Присваиваем названия колонкам вручную
df.columns = ['Предметы', '% оформления заказов', 'Средний дробный рейтинг с продажами']

# Разделяем "Предметы" на "Категория" и "Товар"
df[['Категория', 'Товар']] = df['Предметы'].str.split(' / ', expand=True)

# Преобразуем числовые значения
for col in ['% оформления заказов', 'Средний дробный рейтинг с продажами']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# === Заполняем пропуски (NaN) ===
# Можем выбрать медиану, среднее или 0:
df['% оформления заказов'] = df['% оформления заказов'].fillna(df['% оформления заказов'].median())
df['Средний дробный рейтинг с продажами'] = df['Средний дробный рейтинг с продажами'].fillna(
    df['Средний дробный рейтинг с продажами'].median()
)

# Словарь групп категорий
category_groups = {
    "Мебель": ["Мебель", "Мебель для дома", "Офисная мебель"],
    "Товары для дома": ["Дом", "Посуда", "Хозяйственные товары", "Освещение", "Текстиль", "Интерьер", "Для уборки"],
    "Электроника и техника": ["Электроника", "Бытовая техника", "Аудио", "Компьютеры", "Телефоны", "Фото и видео", "Автоэлектроника", "Телевизоры и аудиотехника"],
    "Одежда": ["Одежда", "Платья", "Футболки", "Джинсы", "Куртки", "Шорты", "Юбки"],
    "Обувь": ["Обувь", "Кроссовки", "Ботинки", "Туфли"],
    "Аксессуары и ювелирка": ["Аксессуары", "Сумки", "Часы", "Очки", "Украшения", "Аксессуары для волос"],
    "Товары для детей": ["Детям", "Игрушки", "Одежда для детей", "Товары для малышей", "Аксессуары для малышей"],
    "Спорт и активный отдых": ["Спорт", "Туризм", "Отдых", "Фитнес", "Спортивная одежда", "Велоспорт"],
    "Стройка": ["Строительство", "Инструменты", "Электрика", "Сантехника", "Строительные материалы"],
    "Сад и садоводство": ["Сад", "Огород", "Дача", "Все для садоводства"],
    "Автомобили и транспорт": ["Автомобильные товары", "Автоэлектроника", "Мото"],
    "Красота и здоровье": ["Косметика", "Здоровье", "Уход", "Гигиена", "Парфюмерия"],
    "Продукты и напитки": ["Продукты", "Напитки", "Еда"],
    "Канцтовары и книги": ["Канцтовары", "Книги", "Творчество", "Офис"],
    "Хобби и развлечения": ["Хобби", "Музыка", "Настольные игры", "Развлечения"],
    "Животные": ["Животные", "Товары для животных"],
    "Прочее": []
}

# Функция для сопоставления группы
def map_to_group(category):
    for group, subcats in category_groups.items():
        if category in subcats:
            return group
    return "Прочее"

df["Категория (группа)"] = df["Категория"].apply(map_to_group)

# Группировка и расчёт средних значений
result = df.groupby("Категория (группа)")[['% оформления заказов', 'Средний дробный рейтинг с продажами']].mean().round(2)

# print(result)



# Оценка риска по отклонению
def assess_risk(actual, average, indicator_name):
    if pd.isna(actual) or pd.isna(average):
        return f"{indicator_name}: ❓ нет данных"
    deviation = (average - actual) / average
    deviation_percent = deviation * 100
    if deviation_percent > 20:
        color = "🔴 высокий риск"
    elif deviation_percent > 10:
        color = "🟡 умеренный риск"
    else:
        color = "🟢 норма"
    return f"{indicator_name}: факт={actual}, среднее={average}, отклонение={deviation_percent:.1f}% → {color}"


# print(f"\n📦 Ключевая категория продавца: {seller_category}")
# print("📊 Оценка рисков:")
# print(assess_risk(actual_rating, avg_rating, "Оценка"))
# print(assess_risk(actual_supp_ratio, avg_supp_ratio, "Процент выкупа"))


def extract_nested(data, keys, default=False):
    """Безопасное извлечение вложенных ключей, разделённых точками."""
    for key in keys.split('.'):
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data

# Список параметров для оценки
parameter_config = [
    ("hasLogo", True, "У продавца загружен логотип"),
    ("hasBanner", True, "У продавца есть баннер (на витрине)"),
    ("banner.hasSiteBanner", True, "Баннер отображается на сайте"),
    ("banner.hasMobileBanner", True, "Баннер отображается в мобильной версии"),
    ("hideSimilarProducts", False, "Скрыты похожие товары"),
    ("chatBetweenSellerAndClient", True, "Активна поддержка чата с клиентом"),
    ("disablingPriceChartProductCard", True, "График цен включён"),
    ("ratingIsInvisible", False, "Рейтинг не виден покупателям")
]


# Указываем путь к файлу (если файл лежит в той же папке, что и скрипт, путь можно не менять)
file_path = 'Истор данные.csv'

# Чтение CSV-файла
df = pd.read_csv(file_path, encoding='utf-8')  # Если возникнет ошибка кодировки, попробуйте 'cp1251'

# Просмотр первых строк
df

from datetime import datetime
# === Шаг 2: Добавим seller_id из URL ===
df["seller_id"] = df["Профиль на сайте Wildberries"].astype(str).str.extract(r'/seller/(\d+)', expand=False)

import numpy as np
# Значения по умолчанию
valuation_now = np.nan
suppRatio_now = np.nan
feedbacks_per_day_now = np.nan
sales_per_day_now = np.nan

rating_then = np.nan
supp_then = np.nan
feedbacks_per_day_then = np.nan
sales_per_day_then = np.nan



import pandas as pd

# Сравнение текущих и прошлых значений с советами
def compare_with_advice(title, current, past):
    if pd.isna(current) or pd.isna(past):
        return {
            "Параметр": title,
            "Пояснение": "Недостаточно данных",
            "Значение": f"{current} / {past}",
            "Оценка": "❓ Недостаточно данных",
            "Цвет": "gray",
            "Совет": "Проверьте корректность данных в системе"
        }

    diff = current - past
    pct_change = (diff / past) * 100

    # Если без изменений
    if pct_change == 0:
        уровень = "➖ без изменений"
        цвет = "blue"
        совет = "Стабильный показатель, но возможны точки роста."
    
    # Если улучшение — всегда зелёный (норма)
    elif pct_change > 0:
        уровень = "🟢 норма"
        цвет = "green"
        совет = "Показатель улучшился. Продолжайте развивать это направление."

    # Если ухудшение — градация риска
    else:
        if abs(pct_change) > 20:
            уровень = "🔴 высокий риск"
            цвет = "red"
            совет = "Значительное отклонение. Требуется анализ и меры."
        elif abs(pct_change) > 10:
            уровень = "🟡 умеренный риск"
            цвет = "orange"
            совет = "Отклонение выше нормы. Рекомендуется обратить внимание."
        else:
            уровень = "🟢 норма"
            цвет = "green"
            совет = "Показатель снизился, но в пределах нормы."

    return {
        "Параметр": title,
        "Пояснение": f"Сравнение: сейчас={current:.2f}, было={past:.2f} (Δ={pct_change:.1f}%)",
        "Значение": f"{current:.2f}",
        "Оценка": уровень,
        "Цвет": цвет,
        "Совет": совет
    }


# === Вспомогательные блоки оценки ===
def format_feedbacks_concentration_result(max_name, max_feedbacks, total_feedbacks, share):
    if share > 40:
        return {
            "Параметр": "Концентрация отзывов по товарам",
            "Пояснение": f"Товар-лидер: {max_name} ({max_feedbacks} отзывов, {share:.1f}% от общего)",
            "Значение": f"{share:.1f}%",
            "Оценка": "⚠️ Высокая концентрация",
            "Цвет": "orange",
            "Совет": "Более 40% отзывов приходится на один товар. Возможен риск зависимости от флагмана. Рассмотрите диверсификацию."
        }
    else:
        return {
            "Параметр": "Концентрация отзывов по товарам",
            "Пояснение": f"Товар-лидер: {max_name} ({max_feedbacks} отзывов, {share:.1f}% от общего)",
            "Значение": f"{share:.1f}%",
            "Оценка": "✅ Норма",
            "Цвет": "green",
            "Совет": "Отзывы распределены равномерно. Концентрация в пределах нормы."
        }

def format_category_concentration_result(num_categories):
    if num_categories == 1:
        return {
            "Параметр": "Товарная концентрация по категориям",
            "Пояснение": "Все товары — в одной категории",
            "Значение": str(num_categories),
            "Оценка": "🔴 Высокий риск",
            "Цвет": "red",
            "Совет": "Рекомендуется расширить ассортимент для снижения рисков."
        }
    elif num_categories == 2:
        return {
            "Параметр": "Товарная концентрация по категориям",
            "Пояснение": "Товары представлены в двух категориях",
            "Значение": str(num_categories),
            "Оценка": "🟡 Умеренный риск",
            "Цвет": "orange",
            "Совет": "Подумайте о диверсификации для устойчивости к изменениям рынка."
        }
    else:
        return {
            "Параметр": "Товарная концентрация по категориям",
            "Пояснение": f"Охват {num_categories} категорий",
            "Значение": str(num_categories),
            "Оценка": "🟢 Норма",
            "Цвет": "green",
            "Совет": "Хорошая диверсификация ассортимента."
        }

def assess_risk_to_dict(actual, average, indicator_name):
    if pd.isna(actual) or pd.isna(average):
        return {
            "Параметр": indicator_name,
            "Пояснение": "Недостаточно данных для сравнения",
            "Значение": f"{actual} / {average}",
            "Оценка": "❓ Нет данных",
            "Цвет": "gray",
            "Совет": "Проверьте корректность показателей"
        }
    deviation_percent = ((average - actual) / average) * 100
    if deviation_percent > 20:
        return {
            "Параметр": indicator_name,
            "Пояснение": f"факт={actual:.2f}, среднее={average:.2f}, отклонение={deviation_percent:.1f}%",
            "Значение": f"{actual:.2f}",
            "Оценка": "🔴 Высокий риск",
            "Цвет": "red",
            "Совет": "Значительное отклонение от среднего. Требуется вмешательство."
        }
    elif deviation_percent > 10:
        return {
            "Параметр": indicator_name,
            "Пояснение": f"факт={actual:.2f}, среднее={average:.2f}, отклонение={deviation_percent:.1f}%",
            "Значение": f"{actual:.2f}",
            "Оценка": "🟡 умеренный риск",
            "Цвет": "orange",
            "Совет": "Отклонение выше нормы. Рекомендуется обратить внимание."
        }
    else:
        return {
            "Параметр": indicator_name,
            "Пояснение": f"факт={actual:.2f}, среднее={average:.2f}, отклонение={deviation_percent:.1f}%",
            "Значение": f"{actual:.2f}",
            "Оценка": "🟢 норма",
            "Цвет": "green",
            "Совет": "Показатель в пределах нормы."
        }


def generate_summary_from_final_df(final_df):
    
    # 1. Выявим параметры, требующие улучшения
    needs_improvement = final_df[
        final_df["Оценка"].isin(["⚠️ Нужно улучшить", "🔴 высокий риск"])
    ]["Пояснение"].tolist()

    # 2. Выявим параметры, которые ухудшились за год
    yearly_decline = final_df[
        final_df["Оценка"] == "🔽 ухудшение"
    ]["Параметр"].tolist()

    # Формируем текст
    result = []

    if needs_improvement:
        result.append("1. Что необходимо сделать для улучшения оценки:")
        result += [f"   • {p}" for p in needs_improvement]
    else:
        result.append("1. Все параметры соответствуют лучшим практикам. Улучшения не требуются.")

    if yearly_decline:
        result.append("2. Обратите внимание на ухудшение показателей за год:")
        result += [f"   • {p}" for p in yearly_decline]
    else:
        result.append("2. Существенного ухудшения год к году не зафиксировано.")

    return "\n".join(result)

def assign_risk_reason(df):
    """
    Добавляет в датафрейм колонку 'Риск', где содержится формулировка проблемы для каждого параметра.
    """
    parameter_to_risk_name = {
        "hasLogo": "Отсутствие фирменного оформления",
        "hasBanner": "Витрина без баннеров",
        "banner.hasSiteBanner": "Нет баннера на сайте",
        "banner.hasMobileBanner": "Нет баннера в мобильной версии",
        "hideSimilarProducts": "Ограниченный выбор товаров",
        "chatBetweenSellerAndClient": "Недоступна клиентская поддержка",
        "disablingPriceChartProductCard": "Скрыт график цен",
        "ratingIsInvisible": "Рейтинг скрыт от покупателей",
        "Оценка (valuation)": "Падение общей оценки продавца",
        "% выкупа (suppRatio)": "Снижение процента выкупа",
        "Отзывов в день": "Падение отзывной активности",
        "Продаж в день": "Снижение продаж в среднем",
        "Концентрация отзывов по товарам": "Концентрация на один товар",
        "Товарная концентрация по категориям": "Слабая диверсификация категорий",
        "Оценка (valuation, отклонение)": "Оценка ниже среднего по категории",
        "Выкуп (suppRatio, отклонение)": "Выкуп ниже среднего по категории",
        "ИТОГО": "ИТОГО"
    }

    df["Риск"] = df["Параметр"].map(parameter_to_risk_name).fillna("Нет формулировки риска.")
    return df

def assign_risk_level(df):
    """
    Добавляет колонку 'Уровень' (цвет: зелёный, жёлтый, красный, серый) на основе значения 'Оценка'.
    Строка с параметром 'ИТОГО' и пустыми значениями не маркируется.
    """
    color_map = {
        "✅ Хорошо": "🟢 Зелёный",
        "✅ Норма": "🟢 Зелёный",
        "🟢 норма": "🟢 Зелёный",
        "🟢 Норма": "🟢 Зелёный",
        "🔼 улучшение": "🟢 Зелёный",
        "➖ без изменений": "🟢 Зелёный",
        "🟡 умеренный риск": "🟡 Желтый",
        "🟡 Умеренный риск": "🟡 Желтый",
        "⚠️ Нужно улучшить": "🟡 Желтый",
        "🔽 ухудшение": "🟡 Желтый",
        "🔴 высокий риск": "🔴 Красный",
        "🔴 Высокий риск": "🔴 Красный",
        "❓ Недостаточно данных": "🟢 Зелёный",
        "❓ нет данных": "🔴 Красный",
        "❓ Нет данных": "🔴 Красный",
        "⚠️ Высокая концентрация": "🔴 Красный"
    }

    def map_level(row):
        if row.get("Параметр") == "ИТОГО" or pd.isna(row.get("Оценка")):
            return None
        return color_map.get(row["Оценка"], "неизвестно")

    df["Уровень"] = df.apply(map_level, axis=1)
    return df


# Вызов:
# print(generate_summary_from_final_df(final_df))

# === Шаг 1: Задание весов ===
weights = {
    "hasLogo": 2, "hasBanner": 2, "banner.hasSiteBanner": 1, "banner.hasMobileBanner": 1,
    "hideSimilarProducts": 1, "chatBetweenSellerAndClient": 3, "disablingPriceChartProductCard": 1,
    "ratingIsInvisible": 3, "Оценка (valuation)": 15, "% выкупа (suppRatio)": 15,
    "Отзывов в день": 15, "Продаж в день": 15,
    "Концентрация отзывов по товарам": 7, "Товарная концентрация по категориям": 7,
    "Оценка (valuation, отклонение)": 6, "Выкуп (suppRatio, отклонение)": 6
}

# === Шаг 2: Присвоим веса и оценки по шкале 0–1
# Формируем отображение для оценки "Оценка" → значение 0–1, если ещё не посчитано
emoji_to_score = {
    "✅ Хорошо": 1.0,
    "✅ Норма": 1.0,
    "🟢 норма": 1.0,
    "🟢 Норма": 1.0,
    "➖ без изменений": 0.7,
    "🔼 улучшение": 1.0,
    "🟡 умеренный риск": 0.5,
    "🟡 Умеренный риск": 0.5,
    "⚠️ Нужно улучшить": 0.0,
    "🔽 ухудшение": 0.3,
    "🔴 Высокий риск": 0.0,
    "🔴 высокий риск": 0.0,
    "❓ Недостаточно данных": 1.0,
    "⚠️ Высокая концентрация": 0.0
}



# 8. Вывод результата
# display(valid_df[["Параметр", "Оценка", "Оценка 0–1", "Вес", "Баллы"]])
# print(f"\n✅ Итоговая оценка продавца (по валидным метрикам): {final_score:.2%}")
def assign_final_level(result_df):
    itogo_index = result_df[result_df["Риск"] == "ИТОГО"].index
    if itogo_index.empty:
        # print("❌ Строка 'ИТОГО' не найдена.")
        return result_df

    idx = itogo_index[0]
    final_score = result_df.at[idx, "Баллы"]

    try:
        final_score = float(final_score)
    except Exception:
        result_df.at[idx, "Уровень"] = "❓ Не удалось определить"
        return result_df

    # Баллы идут по шкале до 100
    if final_score > 85:
        result_df.at[idx, "Уровень"] = "🟢 Надёжный контрагент"
    elif final_score >= 65:
        result_df.at[idx, "Уровень"] = "🟡 Умеренный риск"
    else:
        result_df.at[idx, "Уровень"] = "🔴 Высокий риск"

    return result_df




def run_wb_scoring_advanced(seller_id: int) -> dict:
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import pandas as pd
    # 1. Собираем категории товаров
    names = fetch_all_product_names(seller_id)
    category_counts = analyze_categories_by_name(names)
    num_categories = len(category_counts)

    # 2. Анализ отзывов
    max_name, max_feedbacks, total_feedbacks, share = analyze_feedbacks_concentration(seller_id)

    # 3. Запрашиваем WB API
    data = fetch_wb_raw_data(str(seller_id))
    if not data:
        return {"score": 0, "risks": {"high_risks": ["Ошибка получения данных WB"], "medium_risks": [], "low_risks": []}}

    # Оценка (анализ параметров WB)
    analysis = []
    for key, good_if_true, description in parameter_config:
        value = extract_nested(data, key, default=None)
        is_good = (value if good_if_true else not value)
        status = "✅ Хорошо" if is_good else "⚠️ Нужно улучшить"
        color = "green" if is_good else "orange"
        analysis.append({
            "Параметр": key,
            "Пояснение": description,
            "Значение": value,
            "Оценка": status,
            "Цвет": color
        })
    for row in analysis:
        if row["Оценка"] == "✅ Хорошо":
            row["Совет"] = "Показатель соответствует лучшим практикам"
        else:
            row["Совет"] = "Рекомендуется улучшить данный параметр"
    analysis_df = pd.DataFrame(analysis)
    # 4. Назначаем категорию
    main_category = category_counts.most_common(1)[0][0]

    # 5. Подгружаем Excel с категориями и сравнениями
    try:
        result = pd.read_excel('12.xlsx', header=None)
        result.columns = ['Предметы', '% оформления заказов', 'Средний дробный рейтинг с продажами']
        result[['Категория', 'Товар']] = result['Предметы'].str.split(' / ', expand=True)
        for col in ['% оформления заказов', 'Средний дробный рейтинг с продажами']:
            result[col] = pd.to_numeric(result[col], errors='coerce')
        result['% оформления заказов'] = result['% оформления заказов'].fillna(result['% оформления заказов'].median())
        result['Средний дробный рейтинг с продажами'] = result['Средний дробный рейтинг с продажами'].fillna(result['Средний дробный рейтинг с продажами'].median())

        category_groups = {
            "Мебель": ["Мебель", "Мебель для дома", "Офисная мебель"],
            "Товары для дома": ["Дом", "Посуда", "Хозяйственные товары", "Освещение", "Текстиль", "Интерьер", "Для уборки"],
            "Электроника и техника": ["Электроника", "Бытовая техника", "Аудио", "Компьютеры", "Телефоны", "Фото и видео", "Автоэлектроника", "Телевизоры и аудиотехника"],
            "Одежда": ["Одежда", "Платья", "Футболки", "Джинсы", "Куртки", "Шорты", "Юбки"],
            "Обувь": ["Обувь", "Кроссовки", "Ботинки", "Туфли"],
            "Аксессуары и ювелирка": ["Аксессуары", "Сумки", "Часы", "Очки", "Украшения", "Аксессуары для волос"],
            "Товары для детей": ["Детям", "Игрушки", "Одежда для детей", "Товары для малышей", "Аксессуары для малышей"],
            "Спорт и активный отдых": ["Спорт", "Туризм", "Отдых", "Фитнес", "Спортивная одежда", "Велоспорт"],
            "Стройка": ["Строительство", "Инструменты", "Электрика", "Сантехника", "Строительные материалы"],
            "Сад и садоводство": ["Сад", "Огород", "Дача", "Все для садоводства"],
            "Автомобили и транспорт": ["Автомобильные товары", "Автоэлектроника", "Мото"],
            "Красота и здоровье": ["Косметика", "Здоровье", "Уход", "Гигиена", "Парфюмерия"],
            "Продукты и напитки": ["Продукты", "Напитки", "Еда"],
            "Канцтовары и книги": ["Канцтовары", "Книги", "Творчество", "Офис"],
            "Хобби и развлечения": ["Хобби", "Музыка", "Настольные игры", "Развлечения"],
            "Животные": ["Животные", "Товары для животных"],
            "Прочее": []
        }
        def map_to_group(category):
            for group, subcats in category_groups.items():
                if category in subcats:
                    return group
            return "Прочее"

        result["Категория (группа)"] = result["Категория"].apply(map_to_group)
        grouped = result.groupby("Категория (группа)")[['% оформления заказов', 'Средний дробный рейтинг с продажами']].mean().round(2)
    except Exception:
        grouped = pd.DataFrame()

    from datetime import datetime
    actual_rating = float(data.get("valuation", float("nan")))
    actual_supp_ratio = float(data.get("suppRatio", float("nan")))
    category_row = grouped.loc[main_category] if main_category in grouped.index else pd.Series(dtype='float64')
    avg_rating = category_row.get('Средний дробный рейтинг с продажами', float("nan"))
    avg_supp_ratio = category_row.get('% оформления заказов', float("nan"))

    # === Формирование датафрейма
    from pandas import DataFrame
    results = []

    results.append(format_feedbacks_concentration_result(max_name, max_feedbacks, total_feedbacks, share))
    results.append(format_category_concentration_result(num_categories))
    results.append(assess_risk_to_dict(actual_rating, avg_rating, "Оценка (valuation, отклонение)"))
    results.append(assess_risk_to_dict(actual_supp_ratio, avg_supp_ratio, "Выкуп (suppRatio, отклонение)"))

    df = pd.DataFrame(results)
    df = assign_risk_reason(df)
    df = assign_risk_level(df)

    emoji_to_score = {
        "✅ Хорошо": 1.0, "✅ Норма": 1.0, "🟢 норма": 1.0, "🟢 Норма": 1.0,
        "➖ без изменений": 0.7, "🔼 улучшение": 1.0,
        "🟡 умеренный риск": 0.5, "🟡 Умеренный риск": 0.5,
        "⚠️ Нужно улучшить": 0.0, "🔽 ухудшение": 0.3,
        "🔴 Высокий риск": 0.0, "🔴 высокий риск": 0.0,
        "❓ Недостаточно данных": 1.0, "⚠️ Высокая концентрация": 0.0
    }

    weights = {
        "Концентрация отзывов по товарам": 7,
        "Товарная концентрация по категориям": 7,
        "Оценка (valuation, отклонение)": 6,
        "Выкуп (suppRatio, отклонение)": 6
    }

    df["Оценка 0–1"] = df["Оценка"].map(emoji_to_score)
    df["Вес"] = df["Параметр"].map(weights).fillna(0)
    df["Баллы"] = df["Оценка 0–1"] * df["Вес"]

    total_score = df["Баллы"].sum()
    max_score = df["Вес"].sum()
    final_score = round(total_score / max_score * 100, 2) if max_score else 0

    only_risks = df[df["Уровень"] != "🟢 Зелёный"]
    grouped_risks = {
        "high_risks": only_risks[only_risks["Уровень"] == "🔴 Красный"]["Риск"].tolist(),
        "medium_risks": only_risks[only_risks["Уровень"] == "🟡 Желтый"]["Риск"].tolist(),
        "low_risks": only_risks[only_risks["Уровень"] == "🟢 Зелёный"]["Риск"].tolist()
    }

    return {
        "score": final_score,
        "risks": grouped_risks
    }