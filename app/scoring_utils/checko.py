import requests

API_KEY = "i6tmY6fOsvUe50E8"

async def fetch_checko_data(inn: str) -> dict:
    """Запрашивает данные по ИНН из Checko API."""
    url = f"https://api.checko.ru/v2/person?key={API_KEY}&inn={inn}"

    try:
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json().get("data", {})

            return {
                "Недобросовестный блок": data.get("НедоБлок", "Нет данных"),
                "Массовый руководитель": data.get("МассРуковод", "Нет данных"),
                "Массовый учредитель": data.get("МассУчред", "Нет данных"),
                "Санкции": data.get("Санкции", "Нет данных"),
            }
        else:
            return {"error": f"Ошибка запроса: {response.status_code}"}
    
    except Exception as e:
        return {"error": f"Ошибка запроса: {e}"}