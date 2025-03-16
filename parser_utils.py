import requests

# URL API
url = "https://suppliers-shipment-2.wildberries.ru/api/v1/suppliers/1234773"

headers = {
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "origin": "https://www.wildberries.ru",
    "priority": "u=1, i",
    "referer": "https://www.wildberries.ru/seller/1234773",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "macOS",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "macOS",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "x-client-name": "site"
}

cookies = {
    "_wbauid": "1808014871741023479",
    "_cp": "1"
}

# Отправка GET-запроса
s = requests.Session()
response = s.get(url=url, headers=headers, cookies=cookies)

# Проверка успешности и вывод JSON
if response.status_code == 200:
    data = response.json()
    
    # Извлекаем нужные поля
    valuation = data.get('valuationToHundredths')
    feedbacks_count = data.get('feedbacksCount')
    sale_quantity = data.get('saleItemQuantity')
    
    # Красиво выводим
    print(f"Оценка (valuationToHundredths): {valuation}")
    print(f"Количество отзывов (feedbacksCount): {feedbacks_count}")
    print(f"Количество продаж (saleItemQuantity): {sale_quantity}")
else:
    print(f"Ошибка запроса: {response.status_code}")
