import openpyxl

def get_scoring_from_excel(file_path: str) -> int:
    """
    Получает скоринговую оценку из Excel-файла.
    Читаем значение ячейки A1.

    :param file_path: Путь к Excel-файлу.
    :return: Значение скоринговой оценки (целое число).
    """
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active
        scoring_value = sheet["A1"].value
        wb.close()

        if isinstance(scoring_value, (int, float)):
            return int(scoring_value)
        else:
            raise ValueError("Некорректное значение в A1 (не число)")
    
    except Exception as e:
        print(f"[ERROR] Ошибка при чтении Excel-файла: {e}")
        return 0  # Возвращаем 0, если не удалось прочитать файл

scoring_from_excel = get_scoring_from_excel("Финансовые данные.xlsx")
print(f"Скоринговая оценка из Excel: {scoring_from_excel}")