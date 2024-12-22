import requests

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
            "text": "Ты финансовый консультант. К тебе пришел клиент с причиной низкой скоринговой оценки. Предложи ему пути решения проблемы для повышения скоринговой оценки."
        },
        {
            "role": "user",
            "text": "Отсутствие уставного капитала."
        }
    ]
}


url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Api-Key AQVN2v80bFuxVQGnizZzIzeC6W3l8jZrvmjEIOTk"
}

response = requests.post(url, headers=headers, json=prompt)
result = response.text
print(result)