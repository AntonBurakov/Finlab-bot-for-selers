import requests

async def fetch_wildberries_data(seller_id: str) -> dict:
    """Запрашивает данные о продавце на Wildberries"""
    url = f"https://suppliers-shipment-2.wildberries.ru/api/v1/suppliers/{seller_id}"

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "origin": "https://www.wildberries.ru",
        "priority": "u=1, i",
        "referer": f"https://www.wildberries.ru/seller/{seller_id}",
        "sec-ch-ua": '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133")',
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

    try:
        response = requests.get(url=url, headers=headers, cookies=cookies)

        if response.status_code == 200:
            data = response.json()
            return {
                "valuation": data.get("valuationToHundredths"),
                "feedbacks_count": data.get("feedbacksCount"),
                "sale_quantity": data.get("saleItemQuantity"),
            }
        else:
            return {"error": f"Ошибка запроса: {response.status_code}"}
    
    except Exception as e:
        return {"error": f"Ошибка запроса: {e}"}