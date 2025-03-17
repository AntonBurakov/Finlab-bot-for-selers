import openpyxl

def get_seller_data_from_excel(file_path: str, marketplace_link: str) -> dict:
    """
    Ищет `marketplace_link` в первом столбце Excel-файла и возвращает данные из колонок C и D.

    :param file_path: Путь к Excel-файлу.
    :param marketplace_link: Ссылка на продавца Wildberries.
    :return: Словарь с найденными данными.
    """
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet = wb.active

        for row in sheet.iter_rows(min_row=2, values_only=True):  # Пропускаем заголовок
            if row[0] == marketplace_link:
                wb.close()
                return {
                    "Раздел товаров": row[2],  # Колонка C
                    "Категория товаров": row[3]  # Колонка D
                }

        wb.close()
        return {"error": "Продавец не найден в файле"}
    
    except Exception as e:
        return {"error": f"Ошибка при чтении Excel: {e}"}