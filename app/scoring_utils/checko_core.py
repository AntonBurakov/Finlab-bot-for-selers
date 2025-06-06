#!/usr/bin/env python
# coding: utf-8

# In[1]:


import requests
import datetime

class RiskAnalyzer:
    """Анализатор рисков для ИП и ЮЛ."""

    API_KEY = "FJJWoPhZ5uGUL1ve"
    BASE_URLS = {
        "ИП": "https://api.checko.ru/v2/entrepreneur",
        "ЮЛ": "https://api.checko.ru/v2/company"
    }



    CRITICAL_RISKS_UL = {
        "1. Ограничение доступа к сведениям (ФНС)",
        "2. Ликвидация компании",
        "4. Недостоверные сведения о руководителе",
        "5. Недостоверные сведения об учредителях",
        "6. Записи в реестре банкротств (ЕФРСБ)",
        "7. Включение в реестр недобросовестных поставщиков",
        "8. Дисквалифицированные лица в руководстве",
        "11. Массовый руководитель",
        "12. Массовый учредитель",
        "9. Включение в санкционные списки",
        "10. Нелегальная деятельность на финансовом рынке",
        "18. Компания существует менее 3 месяцев",
    }

    NON_CRITICAL_RISKS_UL = {
        "3. Недостоверные сведения о юридическом адресе",
        "15. Наличие задолженности по налогам",
        "17. Высокая кредитная нагрузка региона (Желтый уровень)",
        "19. Компания существует менее 1 года",
        "20. Нарушения при получении господдержки"
    }

    CRITICAL_RISKS_IP = {
        "1. Ограничение доступа к сведениям (ФНС)",
        "2. Прекращение деятельности",
        "4. Массовый руководитель",
        "5. Массовый учредитель",
        "3. Включение в реестр недобросовестных поставщиков",
        "6. Записи в реестре банкротств (ЕФРСБ)",
        "10. Компания существует менее 3 месяцев"
    }

    NON_CRITICAL_RISKS_IP = {
        "7. Нарушения при получении господдержки",
        "11. Компания существует менее 1 года"
    }

    HIGH_RISK_REGIONS = {
        "Красный": [
            "Карачаево-Черкесская Республика",
            "Республика Марий Эл",
            "Оренбургская область"
        ],
        "Желтый": [
            "Ямало-Ненецкий автономный округ",
            "Орловская область",
            "Чеченская Республика",
            "Калужская область",
            "Астраханская область",
            "Саратовская область",
            "Ханты-Мансийский автономный округ - Югра",
            "Республика Коми",
            "Республика Мордовия",
            "Республика Калмыкия",
            "Кабардино-Балкарская Республика",
            "Ставропольский край"
        ]
    }



    def __init__(self, inn):
        """Определяет тип контрагента и загружает данные."""
        self.inn = inn
        self.entity_type = self.detect_entity_type()
        self.data = self.fetch_data()
        self.is_special_tax_mode_used = False

    def detect_entity_type(self):
        """Определяет, является ли ИНН ИП или ЮЛ."""
        if len(self.inn) == 12:
            return "ИП"
        elif len(self.inn) == 10:
            return "ЮЛ"
        else:
            raise ValueError("ИНН должен содержать 10 (ЮЛ) или 12 (ИП) цифр.")

    def fetch_data(self):
        """Получает данные из API."""
        url = self.BASE_URLS[self.entity_type]
        params = {"key": self.API_KEY, "inn": self.inn}

        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Ошибка {response.status_code}: {response.text}")


    def evaluate_risk_level(self, risk_name, value):
        """Определяет уровень риска."""
        if not value:
            return "Зеленый"
        if self.entity_type == "ИП":
            return "Красный" if risk_name in self.CRITICAL_RISKS_IP else "Желтый"
        return "Красный" if risk_name in self.CRITICAL_RISKS_UL else "Желтый"

    def check_region_risk(self):
        """Проверяет, находится ли контрагент в регионе с высокой кредитной нагрузкой."""
        region_name = self.data["data"].get("Регион", {}).get("Наим", "")

        if region_name in self.HIGH_RISK_REGIONS["Красный"]:
            return "Красный"
        elif region_name in self.HIGH_RISK_REGIONS["Желтый"]:
            return "Желтый"
        return "Зеленый"

    def analyze(self):
        """Определяет, является ли контрагент ИП или ЮЛ, и выполняет соответствующий анализ."""
        if self.entity_type == "ИП":
            risks_evaluated = self.analyze_ip()
        else:
            risks_evaluated = self.analyze_ul()

        print("🔎 **Риски контрагента**\n")
        for key, info in risks_evaluated.items():
            print(f"{key}: {info['Статус']} ({info['Уровень']})")

        print("\n--- Заключение ---\n")
        print(self.generate_risk_conclusion(risks_evaluated))


    def analyze_ip(self):
        """Анализирует риски для индивидуальных предпринимателей (ИП)."""
        region_risk = self.check_region_risk()
        region = self.data["data"].get("Регион", {}).get("Наим", "")
        reg_date = self.data["data"].get("ДатаРег", "2100-01-01")
        company_age = (datetime.date.today() - datetime.datetime.strptime(reg_date, "%Y-%m-%d").date()).days

        risks = {
            "1. Ограничение доступа к сведениям (ФНС)": self.data["data"].get("Статус", {}).get("ОгрДоступ", False),
            "2. Прекращение деятельности": bool(self.data["data"].get("Прекращ", {}).get("Дата")),
            "3. Включение в реестр недобросовестных поставщиков": self.data["data"].get("НедобПост", False),
            "4. Массовый руководитель": self.data["data"].get("МассРуковод", False),
            "5. Массовый учредитель": self.data["data"].get("МассУчред", False),
            "6. Записи в реестре банкротств (ЕФРСБ)": bool(self.data["data"].get("ЕФРСБ")),
            "7. Нарушения при получении господдержки": any(support.get("Наруш", False) for support in self.data["data"].get("ПоддержМСП", [])),
            "10. Компания существует менее 3 месяцев": company_age < 90,
            "11. Компания существует менее 1 года": company_age  < 365,
            "12. Высокая доля просроченной задолженности в общей сумме задолженности по кредитам в регионе": region_risk == "Красный",
            "13. Повышенная доля просроченной задолженности в общей сумме задолженности по кредитам в регионе": region_risk == "Желтый",

        }

        risks_with_levels = {key: {"Статус": "Да" if value else "Нет", "Уровень": self.evaluate_risk_level(key, value)} for key, value in risks.items()}
        return risks_with_levels


    def analyze_ul(self):
        """Анализирует риски для ЮЛ."""

        region_risk = self.check_region_risk()
        region = self.data["data"].get("Регион", {}).get("Наим", "")
        reg_date = self.data["data"].get("ДатаРег", "2100-01-01")
        company_age = (datetime.date.today() - datetime.datetime.strptime(reg_date, "%Y-%m-%d").date()).days

        # Получаем информацию о применяемом особом налоговом режиме
        special_tax_mode = self.data["data"].get("Налоги", {}).get("ОсобРежим", [])

        # Если есть хотя бы один особый налоговый режим, присваиваем True
        self.is_special_tax_mode_used = len(special_tax_mode) > 0 and company_age < 36

        risks = {
            "1. Ограничение доступа к сведениям (ФНС)": self.data["data"].get("Статус", {}).get("ОгрДоступ", False),
            "2. Ликвидация компании": bool(self.data["data"].get("Ликвид", {}).get("Дата")),
            "3. Недостоверные сведения о юридическом адресе": self.data["data"].get("ЮрАдрес", {}).get("Недост", False),
            "4. Недостоверные сведения о руководителе": any(ru.get("Недост", False) for ru in self.data["data"].get("Руковод", [])),
            "5. Недостоверные сведения об учредителях": any(uch.get("Недост", False) for uch in self.data["data"].get("Учред", {}).get("ФЛ", [])),
            "6. Записи в реестре банкротств (ЕФРСБ)": bool(self.data["data"].get("ЕФРСБ")),
            "7. Включение в реестр недобросовестных поставщиков": self.data["data"].get("НедобПост", False),
            "8. Дисквалифицированные лица в руководстве": self.data["data"].get("ДисквЛица", False),
            "9. Включение в санкционные списки": self.data["data"].get("Санкции", False),
            "10. Нелегальная деятельность на финансовом рынке": self.data["data"].get("НелегалФин", False),
            "11. Массовый руководитель": self.data["data"].get("МассРуковод", False),
            "12. Массовый учредитель": self.data["data"].get("МассУчред", False),
            "13. Наличие задолженности по налогам": bool(self.data["data"].get("Налоги", {}).get("СумНедоим", 0)),
            "14. Высокая доля просроченной задолженности в общей сумме задолженности по кредитам в регионе": region_risk == "Красный",
            "15. Повышенная доля просроченной задолженности в общей сумме задолженности по кредитам в регионе": region_risk == "Желтый",
            "16. Компания существует менее 3 месяцев": company_age  < 90,
            "17. Компания существует менее 1 года": company_age  < 365,
            "18. Нарушения при получении господдержки": any(support.get("Наруш", False) for support in self.data["data"].get("ПоддержМСП", [])),
        }

        risks_with_levels = {key: {"Статус": "Да" if value else "Нет", "Уровень": self.evaluate_risk_level(key, value)} for key, value in risks.items()}

        return risks_with_levels

    def generate_risk_conclusion(self, risks_evaluated):
        """Генерирует заключение по рискам."""
        critical_issues = []
        non_critical_issues = []

        for risk, details in risks_evaluated.items():
            if details["Уровень"] == "Красный":
                critical_issues.append(risk)
            elif details["Уровень"] == "Желтый":
                non_critical_issues.append(risk)

        if not critical_issues and not non_critical_issues:
            return "✅ Все риски зеленые! Контрагент ведет прозрачную деятельность."

        elif critical_issues:
            message = "🚨 Обнаружены **критические риски**:\n"
            for issue in critical_issues:
                message += f"- **{issue}** - необходимо срочно решать этот вопрос!\n"
            message += "\n⚠️ Рекомендуется тщательно проверить деятельность контрагента и избегать сотрудничества без дополнительной проверки."
            return message

        elif non_critical_issues:
            message = "⚠️ Обнаружены **некритичные (желтые) риски**:\n"
            for issue in non_critical_issues:
                message += f"- **{issue}** - стоит обратить внимание, но не является критичным.\n"
            return message


    def get_full_risk_dataframe(self):
        """Создаёт DataFrame с полными данными по рискам контрагента."""
        if self.entity_type == "ИП":
            risks = self.analyze_ip()
        else:
            risks = self.analyze_ul()

        rows = []
        for risk_name, values in risks.items():
            rows.append({
                "ИНН": self.inn,
                "Тип": self.entity_type,
                "Описание": risk_name,
                "Сработал": 1 if values["Статус"] == "Да" else 0,
                "Уровень": values["Уровень"]
            })

        return pd.DataFrame(rows)


# In[2]:


import pandas as pd


# ## Подгружаем файл по доходам

# In[5]:


def get_user_revenue_by_inn(df, inn):
    inn = str(inn)

    row = df[df['ИНН'] == inn]

    if not row.empty:
        return row.iloc[0]['Выручка']
    else:
        return '🚨 Выручка не обнаружена'


df_income = pd.read_csv('df_income.csv').drop('Unnamed: 0', axis=1)

df_income['ИНН'] = df_income['ИНН'].apply(lambda x: str(int(x)) if pd.notnull(x) else None)
df_income['ОГРН/ОГРНИП'] = df_income['ОГРН/ОГРНИП'].apply(lambda x: str(int(x)) if pd.notnull(x) else None)

mean_price = df_income.loc[df_income['Средняя цена товаров from 2023'] > 0, 'Средняя цена товаров from 2023'].mean()
df_income['Средняя цена товаров from 2023'] = df_income['Средняя цена товаров from 2023'].replace(0, mean_price)
df_income['Товаров продано'] = df_income['Товаров продано'].replace(0, 1)
# Вычисляем выручку
df_income['Выручка'] = df_income['Товаров продано'] * df_income['Средняя цена товаров from 2023']
df_income


# ## Запускаем по фин рискам и исполнительным производствам и арбитражным делам

# In[6]:


import requests
import pandas as pd


def load_data(table, inn):

    API_KEY = "FJJWoPhZ5uGUL1ve"

    # Базовый URL API
    BASE_URL = f"https://api.checko.ru/v2/{table}"


    params = {
        "key": API_KEY,  
        "inn": inn       
    }

    # Выполняем GET-запрос
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        data = response.json()  
        return data
    else:
        print(f"Ошибка {response.status_code}: {response.text}")

ALL_FINANCIAL_RISKS = [
    "Убыток по прибыли",
    "Нулевая прибыль",
    "Низкая маржинальность",
    "Выручка снизилась вдвое",
    "Выручка снизилась на 20–50%",
    "Дебиторка > 50% выручки",
    "Дебиторка 20–50% выручки",
    "Краткосрочные кредиты > 40%",
    "Краткосрочные кредиты 20–40%",
    "Капитал уменьшился > 10%",
    "Реорганизация"
]

ALL_ENFORCEMENT_RISKS = [
    "Задолженность ≥ 20% от активов",
    "Задолженность 10–20% от активов",
    "Есть долги при нулевой прибыли"
]

ALL_ARBITRATION_RISKS = [
    "Сумма исков ≥ 20% от активов",
    "Сумма исков 10–20% от активов",
    "Сумма исков ≥ 20% от выручки (ИП)",
    "Сумма исков 10–20% от выручки (ИП)",
    "Есть дела при нулевой прибыли"
]

inn_type_dict = {}
company_profits = {}
company_aktiv = {}
company_credit_capacity = {}

def analyze_financials(data, inn):
    risks_result = {risk: {"Статус": "Нет", "Уровень": "Зеленый"} for risk in ALL_FINANCIAL_RISKS}

    if not data or "data" not in data:
        return risks_result

    years = sorted(data["data"].keys(), key=int, reverse=True)
    if not years:
        return risks_result

    latest_year = years[0]
    latest_report = data["data"][latest_year]

    revenue = latest_report.get('2110', 0)
    net_profit = latest_report.get('2400', 0)
    accounts_receivable = latest_report.get('1230', 0)
    short_term_loans = latest_report.get('1510', 0)
    total_loans = latest_report.get('1500', 0)
    total_capital = latest_report.get('1300', 0)
    reorganization = latest_report.get('2510', 0)
    aktiv = latest_report.get('1600', 0)

    company_profits[inn] = net_profit
    company_aktiv[inn] = aktiv

    if net_profit < 0:
        risks_result["Убыток по прибыли"] = {"Статус": "Да", "Уровень": "Красный"}
    elif net_profit == 0:
        risks_result["Нулевая прибыль"] = {"Статус": "Да", "Уровень": "Красный"}
    elif net_profit < (0.1 * revenue):
        risks_result["Низкая маржинальность"] = {"Статус": "Да", "Уровень": "Желтый"}

    if len(years) > 1 :
        prev_year_revenue = data["data"][years[1]].get('2110', 0)
        if prev_year_revenue > 0:
            ratio = revenue / prev_year_revenue
            if ratio <= 0.5:
                risks_result["Выручка снизилась вдвое"] = {"Статус": "Да", "Уровень": "Красный"}
            elif ratio <= 0.8:
                risks_result["Выручка снизилась на 20–50%"] = {"Статус": "Да", "Уровень": "Желтый"}

    if revenue > 0:
        ar_ratio = accounts_receivable / revenue
        if ar_ratio >= 0.5:
            risks_result["Дебиторка > 50% выручки"] = {"Статус": "Да", "Уровень": "Красный"}
        elif ar_ratio > 0.2:
            risks_result["Дебиторка 20–50% выручки"] = {"Статус": "Да", "Уровень": "Желтый"}

    short_term_ratio = total_loans / revenue if revenue else 0
    red_zone_threshold = revenue * 0.4
    remaining_credit_capacity = red_zone_threshold - total_loans
    company_credit_capacity[inn] = remaining_credit_capacity
    if short_term_ratio >= 0.4:
        risks_result["Краткосрочные кредиты > 40%"] = {"Статус": "Да", "Уровень": "Красный"}
    elif short_term_ratio >= 0.2:
        risks_result["Краткосрочные кредиты 20–40%"] = {"Статус": "Да", "Уровень": "Желтый"}

    if len(years) > 1 and years[1] in data["data"]:
        prev_total_capital = data["data"][years[1]].get('1300', 0)
        if prev_total_capital > 0 and total_capital < 0.9 * prev_total_capital:
            risks_result["Капитал уменьшился > 10%"] = {"Статус": "Да", "Уровень": "Красный"}

    if reorganization > 0:
        risks_result["Реорганизация"] = {"Статус": "Да", "Уровень": "Желтый"}

    return risks_result



def analyze_enforcements_structured(data, inn, is_ip, aktiv, net_profit):
    """
    Возвращает словарь всех возможных рисков по исполнительным производствам с уровнями.
    """
    ALL_ENFORCEMENT_RISKS = {
        "Задолженность ≥ 20% от активов": "Зеленый",
        "Задолженность 10–20% от активов": "Зеленый",
        "Есть долги при нулевой прибыли": "Зеленый"
    }

    risks_result = {key: {"Статус": "Нет", "Уровень": value} for key, value in ALL_ENFORCEMENT_RISKS.items()}

    if not data or "data" not in data or "Записи" not in data["data"]:
        return risks_result

    enforcements = data["data"]["Записи"]
    total_cases = len(enforcements)
    total_debt = sum(case.get("СумДолг", 0) for case in enforcements)
    outstanding_debt = sum(case.get("ОстЗадолж", 0) for case in enforcements)

    if not is_ip:
        if net_profit and aktiv:
            if total_debt >= 0.2 * aktiv:
                risks_result["Задолженность ≥ 20% от активов"] = {"Статус": "Да", "Уровень": "Красный"}
            elif total_debt >= 0.1 * aktiv:
                risks_result["Задолженность 10–20% от активов"] = {"Статус": "Да", "Уровень": "Желтый"}
        if net_profit is None or float(net_profit) == 0:
            if total_cases > 0:
                risks_result["Есть долги при нулевой прибыли"] = {"Статус": "Да", "Уровень": "Красный"}

    return risks_result

def analyze_legal_cases_structured(data, inn, is_ip, aktiv, net_profit, user_revenue):
    ALL_ARBITRATION_RISKS = {
        "Сумма исков ≥ 20% от активов": "Зеленый",
        "Сумма исков 10–20% от активов": "Зеленый",
        "Сумма исков ≥ 20% от выручки (ИП)": "Зеленый",
        "Сумма исков 10–20% от выручки (ИП)": "Зеленый",
        "Есть дела при нулевой прибыли": "Зеленый",
        "Невозможно оценить арбитражные риски (нет выручки)": "Красный"
    }

    risks_result = {key: {"Статус": "Нет", "Уровень": value} for key, value in ALL_ARBITRATION_RISKS.items()}

    if not data or "data" not in data or "Записи" not in data["data"]:
        return risks_result  # нет дел — возвращаем все с "Нет"

    cases = data["data"]["Записи"]
    total_cases = len(cases)
    total_claims = sum(case.get("СуммИск", 0) for case in cases)

    # --- ЮЛ ---
    if not is_ip:
        if net_profit is not None and aktiv is not None:
            if total_claims >= 0.2 * aktiv:
                risks_result["Сумма исков ≥ 20% от активов"] = {"Статус": "Да", "Уровень": "Красный"}
            elif total_claims >= 0.1 * aktiv:
                risks_result["Сумма исков 10–20% от активов"] = {"Статус": "Да", "Уровень": "Желтый"}
        if net_profit is None or float(net_profit) == 0:
            if total_cases > 0:
                risks_result["Есть дела при нулевой прибыли"] = {"Статус": "Да", "Уровень": "Красный"}

    # --- ИП ---
    if is_ip:
        try:
            user_revenue_val = float(user_revenue)
            if total_claims >= 0.2 * user_revenue_val:
                risks_result["Сумма исков ≥ 20% от выручки (ИП)"] = {"Статус": "Да", "Уровень": "Красный"}
            elif total_claims >= 0.1 * user_revenue_val:
                risks_result["Сумма исков 10–20% от выручки (ИП)"] = {"Статус": "Да", "Уровень": "Желтый"}
            else:
                # зелёный оставляем как есть
                pass
        except (TypeError, ValueError):
            risks_result["Невозможно оценить арбитражные риски (нет выручки)"] = {"Статус": "Да", "Уровень": "Красный"}

    return risks_result


def get_loan_amount(inn, loan_amount_dict):
    """Получает сумму кредита для данного ИНН из словаря."""
    amount = loan_amount_dict.get(inn)
    if amount is None or amount <= 0:
        print(f"[⚠️] Нет суммы кредита для ИНН {inn}")
        return 0.0
    else:
        print(f"[💰] ИНН {inn}: сумма кредита {amount:,.0f} руб.".replace(",", " "))
        return float(amount)

'''
def get_loan_amount(inn):
    """Берёт сумму кредита из credit_dict для данного ИНН. 
    ИСПОЛЬЗУЕМ ТОЛЬКО ДЛЯ ML ИНАЧЕ БЕРЕМ ПРЕДЫДУЩУЮ"""
    amount = credit_dict.get(inn)
    if amount is None or amount <= 0:
        print(f"[⚠️] Нет суммы кредита для ИНН {inn}")
        return 0.0
    else:
        print(f"[💰] ИНН {inn}: сумма кредита {amount:,.0f} руб.".replace(",", " "))
        return float(amount)
'''

def analyze_company_to_dataframe(inn, loan_amount_dict):
    is_ip = len(inn) == 12 or inn_type_dict.get(inn, {}).get("Спецрежим") is True
    user_loan_amount = get_loan_amount(inn, loan_amount_dict) #убрать и заменить при использовании не для ML
    user_revenue = None
    rows = []

    # --- Финансы ---
    if not is_ip:
        fin_data = load_data("finances", inn)
        fin_risks = analyze_financials(fin_data, inn)
        for risk_name, status in fin_risks.items():
            rows.append({
                "ИНН": inn,
                "Тип": "ЮЛ",
                "Описание": risk_name,
                "Сработал": 1 if status["Статус"] == "Да" else 0,
                "Уровень": status["Уровень"]
            })


    if is_ip:
        user_revenue = get_user_revenue_by_inn(df_income, inn)
        try:
            user_revenue = float(user_revenue)
        except (TypeError, ValueError):
            user_revenue = None

    # --- Анализ кредитной нагрузки ---
    if is_ip:

        if user_revenue is None:
            rows.append({
                "ИНН": inn, "Тип": "ИП",
                "Описание": "Невозможно оценить кредитную нагрузку (нет выручки ИП)",
                "Сработал": 1,
                "Уровень": "Красный"
            })
        else:      

            try:
                loan_ratio = user_loan_amount / float(user_revenue)
            except (TypeError, ValueError):
                loan_ratio = None

            if loan_ratio is None or loan_ratio >= 0.2:
                rows.append({
                    "ИНН": inn, "Тип": "ИП",
                    "Описание": f"Объем кредита составляет больше 20% от выручки ИП.",
                    "Сработал": 1, "Уровень": "Красный"
                })
            elif loan_ratio >= 0.1:
                rows.append({
                    "ИНН": inn, "Тип": "ИП",
                    "Описание": f"Объем кредита составляет больше 10% от выручки ИП.",
                    "Сработал": 1, "Уровень": "Желтый"
                })
            else:
                rows.append({
                    "ИНН": inn, "Тип": "ИП",
                    "Описание": f"Объем кредита составляет меньше 10% от выручки ИП.",
                    "Сработал": 0, "Уровень": "Зеленый"
                })


    else:
        allowed_credit = company_credit_capacity.get(inn)

        if allowed_credit is not None:
            if allowed_credit < 0 or user_loan_amount > allowed_credit:
                rows.append({
                    "ИНН": inn, "Тип": "ЮЛ",
                    "Описание": f"Кредит превышает допустимую нагрузку.",
                    "Сработал": 1, "Уровень": "Красный"
                })
            else:
                rows.append({
                    "ИНН": inn, "Тип": "ЮЛ",
                    "Описание": f"Кредит в пределах допустимой нагрузки.).",
                    "Сработал": 0, "Уровень": "Зеленый"
                })


    # --- Загрузка данных ---
    ar_data = load_data("legal-cases", inn)

    # --- Исполнительные ---
    if not is_ip:
        en_data = load_data("enforcements", inn)
        en_risks = analyze_enforcements_structured(en_data, inn, is_ip, company_aktiv.get(inn), company_profits.get(inn))
        for risk_name, status in en_risks.items():
            rows.append({
                "ИНН": inn,
                "Тип": "ИП" if is_ip else "ЮЛ",
                "Описание": risk_name,
                "Сработал": 1 if status["Статус"] == "Да" else 0,
                "Уровень": status["Уровень"]
            })

    # --- Арбитраж ---
    ar_risks = analyze_legal_cases_structured(ar_data, inn, is_ip, company_aktiv.get(inn), company_profits.get(inn), user_revenue)
    for risk_name, status in ar_risks.items():
        # Пропускаем риски, не относящиеся к данному типу
        if is_ip and any(substr in risk_name.lower() for substr in ["актив", "нулевой прибыли"]):
            continue
        if not is_ip and "выручк" in risk_name.lower():
            continue
        if not is_ip and "арбитражные риски" in risk_name.lower():
            continue


        rows.append({
            "ИНН": inn,
            "Тип": "ИП" if is_ip else "ЮЛ",
            "Описание": risk_name,
            "Сработал": 1 if status["Статус"] == "Да" else 0,
            "Уровень": status["Уровень"]
        })

    return pd.DataFrame(rows)


# In[7]:




# In[8]:


def assign_usn_type(df_all):
    """
    Если для одного ИНН в df_all есть и ЮЛ, и ИП — присваиваем 'УСН' как тип всем строкам с этим ИНН.
    """
    # Группируем по ИНН и получаем множество типов для каждого ИНН
    inn_type_map = df_all.groupby("ИНН")["Тип"].agg(set)

    # Определяем ИНН, у которых типы одновременно ИП и ЮЛ
    usn_inns = inn_type_map[inn_type_map.apply(lambda x: {"ЮЛ", "ИП"}.issubset(x))].index

    # Присваиваем "УСН" всем строкам с такими ИНН
    df_all.loc[df_all["ИНН"].isin(usn_inns), "Тип"] = "УСН"

    return df_all



# # Оценка

# In[11]:


RISK_GROUPS_YUL = {
    "Риски правового статуса": [
        "1. Ограничение доступа к сведениям (ФНС)",
        "2. Ликвидация компании",
        "3. Недостоверные сведения о юридическом адресе",
        "4. Недостоверные сведения о руководителе",
        "5. Недостоверные сведения об учредителях",
        "6. Записи в реестре банкротств (ЕФРСБ)",
        "7. Включение в реестр недобросовестных поставщиков",
        "8. Дисквалифицированные лица в руководстве",
        "9. Включение в санкционные списки",
        "10. Незаконная деятельность на финансовом рынке",
        "11. Массовый учредитель",
        "12. Массовый руководитель",
        "13. Наличие задолженности по налогам",
        "16. Компания существует менее 3 месяцев",
        "17. Компания существует менее 1 года",
        "18. Нарушения при получении господдержки"
    ],
    "Региональный риск": [
        "14. Высокая доля просроченной задолженности в общей сумме задолженности по кредитам в регионе",
        "15. Повышенная доля просроченной задолженности в общей сумме задолженности по кредитам в регионе"
    ],
    "Риски прибыли": [
        "Убыток по прибыли",
        "Нулевая прибыль",
        "Низкая маржинальность"
    ],
    "Снижение выручки": [
        "Выручка снизилась на 20–50%",
        "Выручка снизилась вдвое"
    ],
    "Дебиторская нагрузка": [
        "Дебиторка > 50% выручки",
        "Дебиторка 20–50% выручки"
    ],
    "Краткосрочные кредиты": [
        "Краткосрочные кредиты > 40%",
        "Краткосрочные кредиты 20–40%"
    ],
    "Капитал/реорганизация": [
        "Капитал уменьшился > 10%",
        "Реорганизация"
    ],
    "Кредитная нагрузка": [
        "Кредит превышает допустимую нагрузку.",
        "Кредит в пределах допустимой нагрузки.)."
    ],
    "Задолженность по исполнительным производствам": [
        "Задолженность ≥ 20% от активов",
        "Задолженность 10–20% от активов",
        "Есть долги при нулевой прибыли"
    ],
    "Арбитражные риски": [
        "Сумма исков ≥ 20% от активов",
        "Сумма исков 10–20% от активов",
        "Есть дела при нулевой прибыли"
    ]
}

RISK_GROUP_WEIGHTS = {
    "Риски правового статуса": 25,
    "Риски прибыли": 15,
    "Кредитная нагрузка": 25,
    "Задолженность по исполнительным производствам": 5,
    "Региональный риск": 2,
    "Снижение выручки": 5,
    "Дебиторская нагрузка": 10,
    "Краткосрочные кредиты": 5,
    "Капитал/реорганизация": 3,
    "Арбитражные риски": 5
}
def evaluate_yul_score(df_all, risk_groups, group_weights):

    """
    Оценка ЮЛ с учётом обновлённой логики:
    - Красный (сработал) обнуляет блок
    - Жёлтый (сработал хотя бы один) — баллы делятся на 2
    - Зелёный (сработал) начисляется
    - Если никто не сработал — начисляется весь вес
    """
    total_score = 0
    group_results = []

    for group_name, risk_list in risk_groups.items():
        group_df = df_all[df_all["Описание"].isin(risk_list)]
        group_weight = group_weights.get(group_name, 0)
        n_risks = len(risk_list)

        if n_risks == 0 or group_df.empty:
            applied_score = 0
            status = "⚪️ Нет данных по группе"
        else:
            per_risk_weight = group_weight / n_risks

            red_triggered = group_df[(group_df["Уровень"] == "Красный") & (group_df["Сработал"] == 1)]

            if not red_triggered.empty:
                applied_score = 0
                status = "🔴 Сработал красный риск — блок обнулён"
            else:
                green_triggered = group_df[(group_df["Уровень"] == "Зеленый") & (group_df["Сработал"] == 1)]
                yellow_triggered = group_df[(group_df["Уровень"] == "Желтый") & (group_df["Сработал"] == 1)]


                if group_df["Сработал"].sum() == 0:
                    applied_score = group_weight
                    status = f"🟢 Ни один риск не сработал — блок засчитан полностью ({applied_score:.2f})"
                else:
                    applied_score = group_weight
                    if not yellow_triggered.empty:
                        applied_score = group_weight / (yellow_triggered['Сработал'].sum() * 2)  
                        status = f"🟢 Зелёные: {group_weight:.2f} | 🟡 Делим на 2 из-за {yellow_triggered['Сработал'].sum()} жёлтого/ых → {applied_score:.2f}"
                    elif len(green_triggered) > 0:
                        status = f"🟢 {len(green_triggered)} зелёных риска — {applied_score:.2f} баллов"
                    else:
                        status = "⚪️ Нет сработавших зелёных — баллов не начислено"

        total_score += applied_score
        group_results.append(f"{group_name}: {round(applied_score, 2)} баллов ({status})")

    if total_score >= 90:
        label = "🟢 Надёжный контрагент"
    elif total_score >= 70:
        label = "🟡 Умеренный риск"
    else:
        label = "🔴 Высокий риск"

    return {
        "📊 Итоговая оценка": f"{round(total_score, 2)}/100",
        "🎯 Интерпретация": label,
        "📋 Детализация по блокам": group_results
    }


def evaluate_ip_score(df_all):
    """
    Оценка ИП по 3 блокам:
    - Правовой статус (30 баллов)
    - Кредитная нагрузка (50 баллов)
    - Арбитражные риски (20 баллов)

    Обновлённая логика:
    - Красный сработал → обнуляется весь блок
    - Жёлтые сработали → вес блока / (кол-во жёлтых * 2)
    - Только зелёные → начисляется весь вес
    - Если никто не сработал → начисляется весь вес
    """
    risk_groups = {
        "Правовой статус": [
            "1. Ограничение доступа к сведениям (ФНС)",
            "2. Прекращение деятельности",
            "3. Включение в реестр недобросовестных поставщиков (РНП)",
            "4. Массовый руководитель",
            "5. Массовый учредитель",
            "6. Записи в реестре банкротств (ЕФРСБ)",
            "7. Нарушения при получении господдержки",
            "10. Компания существует менее 3 месяцев",
            "11. Компания существует менее 1 года",
            "12. Высокая доля просроченной задолженности в ФССП",
            "13. Повышенная доля просроченной задолженности в ФССП"
        ],
        "Кредитная нагрузка": [
            "Объем кредита составляет меньше 10% от выручки ИП.",
            "Объем кредита составляет больше 10% от выручки ИП.",
            "Объем кредита составляет больше 20% от выручки ИП."


        ],
        "Арбитражные риски": [
            "Сумма исков ≥ 20% от выручки (ИП)",
            "Сумма исков 10–20% от выручки (ИП)",
            "Невозможно оценить арбитражные риски (нет выручки)"
        ]
    }


    group_weights = {
        "Правовой статус": 50,
        "Кредитная нагрузка": 30,
        "Арбитражные риски": 20
    }

    total_score = 0
    group_results = []

    for group_name, risk_list in risk_groups.items():
        group_df = df_all[df_all["Описание"].isin(risk_list)]
        group_weight = group_weights[group_name]

        if group_df.empty:
            applied_score = 0
            status = "⚪️ Нет данных по группе"
        else:
            red_triggered = group_df[(group_df["Уровень"] == "Красный") & (group_df["Сработал"] == 1)]

            if not red_triggered.empty:
                applied_score = 0
                status = "🔴 Сработал красный риск — блок обнулён"
            else:
                yellow_triggered = group_df[(group_df["Уровень"] == "Желтый") & (group_df["Сработал"] == 1)]
                green_triggered = group_df[(group_df["Уровень"] == "Зеленый") & (group_df["Сработал"] == 1)]

                total_triggered = group_df["Сработал"].sum()

                if total_triggered == 0:
                    applied_score = group_weight
                    status = f"🟢 Ни один риск не сработал — блок засчитан полностью ({applied_score:.2f})"
                elif not yellow_triggered.empty:
                    n_yellow = yellow_triggered["Сработал"].sum()
                    applied_score = round(group_weight / (n_yellow * 2), 2)
                    status = f"🟡 {n_yellow} жёлтых риска — делим на {n_yellow * 2} → {applied_score:.2f}"
                else:
                    applied_score = group_weight
                    status = f"🟢 Только зелёные — блок засчитан полностью ({applied_score:.2f})"

        total_score += applied_score
        group_results.append(f"{group_name}: {applied_score} баллов ({status})")

    if total_score >= 90:
        label = "🟢 Надёжный субъект"
    elif total_score >= 70:
        label = "🟡 Умеренный риск"
    else:
        label = "🔴 Высокий риск"

    return {
        "📊 Итоговая оценка": f"{round(total_score, 2)}/100",
        "🎯 Интерпретация": label,
        "📋 Детализация по блокам": group_results
    }

def evaluate_usn_score(df_all):
    """
    Оценка УСН-контрагента:
    - Правовые риски — 45 баллов
    - Региональные риски — 5 баллов
    - Финансовые риски (кредит + арбитраж) — 50 баллов

    Логика:
    - Красный сработал — блок = 0
    - Жёлтые — блок / (кол-во жёлтых * 2)
    - Только зелёные или ничего не сработало — весь вес
    """
    risk_groups = {
        "Правовые риски": [
            "1. Ограничение доступа к сведениям (ФНС)",
            "2. Ликвидация компании",
            "3. Недостоверные сведения о юридическом адресе",
            "4. Недостоверные сведения о руководителе",
            "5. Недостоверные сведения об учредителях",
            "6. Записи в реестре банкротств (ЕФРСБ)",
            "7. Включение в реестр недобросовестных поставщиков (РНП)",
            "8. Дисквалифицированные лица в руководстве",
            "9. Включение в санкционные списки",
            "10. Нелегальная деятельность на финансовом рынке",
            "11. Массовый руководитель",
            "12. Массовый учредитель",
            "13. Наличие задолженности по налогам",
            "18. Нарушения при получении господдержки"
        ],
        "Региональные риски": [
            "14. Высокая доля просроченной задолженности в ФССП",
            "15. Повышенная доля просроченной задолженности в ФССП",
            "16. Компания существует менее 3 месяцев",
            "17. Компания существует менее 1 года"
        ],
        "Финансовые риски": [
            "Объем кредита составляет больше 10% от выручки ИП.",
            "Сумма исков ≥ 20% от выручки (ИП)",
            "Сумма исков 10–20% от выручки (ИП)",
            "Невозможно оценить арбитражные риски (нет выручки)",      
            "Объем кредита составляет больше 10% от выручки ИП.",
            "Объем кредита составляет больше 20% от выручки ИП."

        ]
    }

    group_weights = {
        "Правовые риски": 45,
        "Региональные риски": 5,
        "Финансовые риски": 50
    }

    total_score = 0
    group_results = []

    for group_name, risk_list in risk_groups.items():
        group_df = df_all[df_all["Описание"].isin(risk_list)]
        group_weight = group_weights[group_name]

        if group_df.empty:
            applied_score = 0
            status = "⚪️ Нет данных по группе"
        else:
            red_triggered = group_df[(group_df["Уровень"] == "Красный") & (group_df["Сработал"] == 1)]

            if not red_triggered.empty:
                applied_score = 0
                status = "🔴 Сработал красный риск — блок обнулён"
            else:
                yellow_triggered = group_df[(group_df["Уровень"] == "Желтый") & (group_df["Сработал"] == 1)]
                green_triggered = group_df[(group_df["Уровень"] == "Зеленый") & (group_df["Сработал"] == 1)]

                total_triggered = group_df["Сработал"].sum()

                if total_triggered == 0:
                    applied_score = group_weight
                    status = f"🟢 Ни один риск не сработал — блок засчитан полностью ({applied_score:.2f})"
                elif not yellow_triggered.empty:
                    n_yellow = yellow_triggered["Сработал"].sum()
                    applied_score = round(group_weight / (n_yellow * 2), 2)
                    status = f"🟡 {n_yellow} жёлтых риска — делим на {n_yellow * 2} → {applied_score:.2f}"
                else:
                    applied_score = group_weight
                    status = f"🟢 Только зелёные — блок засчитан полностью ({applied_score:.2f})"

        total_score += applied_score
        group_results.append(f"{group_name}: {applied_score} баллов ({status})")

    if total_score >= 90:
        label = "🟢 Надёжный субъект"
    elif total_score >= 70:
        label = "🟡 Умеренный риск"
    else:
        label = "🔴 Высокий риск"

    return {
        "📊 Итоговая оценка": f"{round(total_score, 2)}/100",
        "🎯 Интерпретация": label,
        "📋 Детализация по блокам": group_results
    }

def evaluate_by_type(df_all, yul_groups=None, yul_weights=None):
    """
    Определяет тип контрагента и вызывает нужную функцию:
    - ЮЛ — evaluate_yul_score
    - ИП — evaluate_ip_score
    - УСН — evaluate_usn_score

    Аргументы:
    - df_all — DataFrame для одного ИНН (одного контрагента)
    - yul_groups, yul_weights — группы и веса для ЮЛ
    """
    type_set = set(df_all["Тип"].unique())

    if "УСН" in type_set:
        return evaluate_usn_score(df_all)
    elif "ИП" in type_set:
        return evaluate_ip_score(df_all)
    elif "ЮЛ" in type_set:
        if yul_groups is None or yul_weights is None:
            raise ValueError("Для оценки ЮЛ нужно передать risk_groups и group_weights")
        return evaluate_yul_score(df_all, yul_groups, yul_weights)
    else:
        raise ValueError(f"Неизвестный тип субъекта: {type_set}")

def summarize_one(df_one, yul_groups, yul_weights):
    """
    Обработка одного ИНН → возвращает одну строку DataFrame
    """
    result = evaluate_by_type(df_one, yul_groups, yul_weights)
    score_str = result["📊 Итоговая оценка"]
    score_value = float(score_str.split("/")[0])
    risk_label = result["🎯 Интерпретация"]
    subject_type = df_one["Тип"].iloc[0]
    inn = df_one["ИНН"].iloc[0]

    return pd.DataFrame([{
        "ИНН": inn,
        "Тип": subject_type,
        "Оценка": score_value,
        "Риск": risk_label
    }])


# In[12]:




# In[10]:




def run_checko_scoring(inn: str, loan_amount: float = 0.0) -> dict:
    """
    Универсальный вызов скоринга Checko.
    Возвращает нормированный скоринг и список рисков по ИНН по цветам.
    """
    analyzer = RiskAnalyzer(inn)

    # Сохраняем тип контрагента
    inn_type_dict[inn] = {
        "Тип": analyzer.entity_type,
        "Спецрежим": analyzer.is_special_tax_mode_used
    }

    # Основные и дополнительные риски
    df_main = analyzer.get_full_risk_dataframe()
    loan_amount_dict = {inn: loan_amount}
    df_extra = analyze_company_to_dataframe(inn, loan_amount_dict)

    df_all = pd.concat([df_main, df_extra])
    df_all = assign_usn_type(df_all)

    # Выделяем только риски, которые сработали
    df_only_risks = df_all[df_all['Сработал'] == 1]

    summary_df = summarize_one(df_all, RISK_GROUPS_YUL, RISK_GROUP_WEIGHTS)
    score = float(summary_df["Оценка"].iloc[0]) / 100

    # Категоризация рисков
    risk_groups = {
        "high_risks": df_only_risks[df_only_risks["Уровень"] == "Красный"]["Описание"].tolist(),
        "medium_risks": df_only_risks[df_only_risks["Уровень"] == "Желтый"]["Описание"].tolist(),
        "low_risks": df_only_risks[df_only_risks["Уровень"] == "Зеленый"]["Описание"].tolist()
    }

    return {
        "score": score,
        "risks": risk_groups
    }
