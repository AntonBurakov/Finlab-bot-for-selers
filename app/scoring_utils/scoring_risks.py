class RiskAnalysis:
    def __init__(self):
        self.low_risks = []
        self.medium_risks = []
        self.high_risks = []

    def add_risk(self, level: str, description: str):
        """Добавляет риск в соответствующую категорию"""
        if level == "low":
            self.low_risks.append(description)
        elif level == "medium":
            self.medium_risks.append(description)
        elif level == "high":
            self.high_risks.append(description)

    def analyze(self, data: dict):
        """
        Анализирует собранные данные и добавляет риски.
        :param data: Собранные данные по продавцу.
        """

        # **🔴 Высокий риск**: низкий рейтинг на Wildberries (< 3.5)
        if float(data.get("valuation", 5.0)) < 3.5:
            self.add_risk("high", "Низкий рейтинг продавца на Wildberries (< 3.5)")

        # **🟠 Средний риск**: много негативных отзывов (> 5000)
        if data.get("feedbacks_count", 0) > 5000:
            self.add_risk("high", "Сумма исков превышает 2 млн рублей")

        # **🟡 Низкий риск**: низкие продажи (< 1000)
        if data.get("sale_quantity", 0) < 1000:
            self.add_risk("low", "Истекшие лицензии")

        # **🔴 Высокий риск**: продавец числится в массовых руководителях
        if data.get("mass_rukovod", False):
            self.add_risk("high", "Продавец является массовым руководителем")

        # **🔴 Высокий риск**: есть санкции
        if data.get("sanctions", False):
            self.add_risk("high", "На продавца наложены санкции")

        # **🟠 Средний риск**: товар в категории с высоким количеством жалоб (например, одежда)
        risky_categories = ["Одежда", "Обувь"]
        if data.get("category", "") in risky_categories:
            self.add_risk("medium", "Продавец работает в категории с повышенным уровнем жалоб")

    def get_results(self):
        """Возвращает список рисков по категориям"""
        return {
            "low_risks": self.low_risks,
            "medium_risks": self.medium_risks,
            "high_risks": self.high_risks
        }