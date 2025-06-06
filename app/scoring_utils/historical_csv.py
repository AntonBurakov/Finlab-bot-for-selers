import csv

def get_seller_data_from_csv(filename: str, profile_link: str) -> dict:
    with open(filename, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Профиль на сайте Wildberries"] == profile_link:
                high_risks = []
                medium_risks = []

                for col, value in row.items():
                    if "Риск по параметру" in col and value:
                        value = value.strip()
                        if value.startswith("Высокий риск:"):
                            high_risks.append(value)
                        elif value.startswith("Умеренный риск:"):
                            medium_risks.append(value)

                return {
                    "Категория товаров": row.get("Категория товаров", "Нет данных"),
                    "Раздел товаров": row.get("Раздел товаров", "Нет данных"),
                    "csv_high_risks": high_risks,   # 🔥 отдельный список высоких
                    "csv_medium_risks": medium_risks,  # 🔥 отдельный список умеренных
                    "score": row.get("Баллов по скоринговой карте")
                }

    return {}