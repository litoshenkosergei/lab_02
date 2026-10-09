import os

# Глобальная константа со множеством допустимых статусов заказов
VALID_STATUSES = {"новый", "в обработке", "выполнен", "отменён"}

def get_cost_category(cost):
    """Определение категории стоимости заказа по граничным значениям."""
    if cost < 1000.0:
        return "Малый"
    elif cost < 5000.0:
        return "Средний"
    else:
        return "Крупный"

def parse_and_validate_record(line, line_num, existing_ids):
    """Разбор одной строки файла, валидация по ТЗ и возврат словаря или ошибки."""
    line = line.strip()
    if not line:
        return None, None

    fields = []
    for f in line.split(';'):
        fields.append(f.strip())

    # 1. Проверка количества полей
    if len(fields) != 6:
        return None, f"Строка {line_num}: неверное количество полей (должно быть 6)."

    raw_id, raw_customer, raw_category, raw_quantity, raw_price, raw_status = fields

    # 2. Проверка обязательных текстовых полей
    if not raw_customer:
        return None, f"Строка {line_num}: имя покупателя не может быть пустым."
    if not raw_category:
        return None, f"Строка {line_num}: категория товара не может быть пустой."

    # 3. Валидация ID (положительное целое)
    try:
        order_id = int(raw_id)
        if order_id <= 0:
            return None, f"Строка {line_num}: номер заказа должен быть положительным целым числом."
    except ValueError:
        return None, f"Строка {line_num}: невозможно преобразовать номер заказа в целое число."

    # 4. Валидация количества (положительное целое)
    try:
        quantity = int(raw_quantity)
        if quantity <= 0:
            return None, f"Строка {line_num}: количество должно быть положительным целым числом."
    except ValueError:
        return None, f"Строка {line_num}: количество должно быть целым числом."

    # 5. Валидация цены (положительное float)
    try:
        price = float(raw_price)
        if price <= 0:
            return None, f"Строка {line_num}: цена должна быть положительным числом."
    except ValueError:
        return None, f"Строка {line_num}: невозможно преобразовать цену в число с плавающей точкой."

    # 6. Валидация статуса без учёта регистра
    status_lower = raw_status.lower()
    if status_lower not in VALID_STATUSES:
        return None, f"Строка {line_num}: неизвестный статус «{raw_status}»."

    # 7. Проверка на уникальность номера заказа
    if order_id in existing_ids:
        return None, f"Строка {line_num}: повторяющийся номер заказа {order_id}."

    # Вычисляемые показатели
    cost = round(quantity * price, 2)
    cost_category = get_cost_category(cost)

    record = {
        "id": order_id,
        "customer": raw_customer,
        "category": raw_category,
        "quantity": quantity,
        "price": price,
        "status": status_lower,
        "cost": cost,
        "cost_category": cost_category
    }
    return record, None

def load_orders(file_path):
    """Безопасное чтение файла orders.txt и наполнение коллекций данных."""
    orders = []
    errors = []
    existing_ids = set()

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Входной файл '{file_path}' не найден.")

    with open(file_path, mode='r', encoding='utf-8') as f:
        for idx, line in enumerate(f, start=1):
            record, error_msg = parse_and_validate_record(line, idx, existing_ids)
            if error_msg:
                errors.append(error_msg)
            elif record:
                orders.append(record)
                existing_ids.add(record["id"])
    return orders, errors
def sort_orders_by_cost(orders):
    """Сортировка: по убыванию стоимости, затем по возрастанию ID."""
    return sorted(orders, key=lambda x: (-x["cost"], x["id"]))

def sort_orders_by_category_and_name(orders):
    """Сортировка: по категории, затем по имени покупателя."""
    return sorted(orders, key=lambda x: (x["category"].lower(), x["customer"].lower()))

def filter_by_status(orders, status):
    """Регистронезависимая фильтрация по статусу заказа."""
    result = []
    search_status = status.strip().lower()
    for o in orders:
        if o["status"] == search_status:
            result.append(o)
    return result

def filter_by_category(orders, category):
    """Регистронезависимая фильтрация по категории товара."""
    result = []
    search_cat = category.strip().lower()
    for o in orders:
        if o["category"].lower() == search_cat:
            result.append(o)
    return result

def search_by_customer_name(orders, name_part):
    """Поиск заказов по части имени покупателя."""
    result = []
    search_name = name_part.strip().lower()
    for o in orders:
        if search_name in o["customer"].lower():
            result.append(o)
    return result

def get_large_orders(orders):
    """Получение списка крупных заказов (стоимость >= 5000)."""
    result = []
    for o in orders:
        if o["cost"] >= 5000.0:
            result.append(o)
    return result

def get_unique_categories(orders):
    """Получение отсортированного списка уникальных категорий."""
    categories_set = set()
    for o in orders:
        categories_set.add(o["category"])
    return sorted(list(categories_set))

def calculate_general_metrics(orders):
    """Расчёт общих экономических и статистических показателей."""
    if not orders:
        return {}

    total_orders = len(orders)
    completed_orders = []
    cancelled_orders = []
    total_cost = 0.0
    revenue = 0.0

    for o in orders:
        total_cost += o["cost"]
        if o["status"] == "выполнен":
            completed_orders.append(o)
            revenue += o["cost"]
        elif o["status"] == "отменён":
            cancelled_orders.append(o)

    avg_cost = round(total_cost / total_orders, 2)
    
    most_expensive = orders[0] if orders else {}
    for o in orders:
        if o["cost"] > most_expensive["cost"]:
            most_expensive = o

    # Анализ топ-покупателей по выполненным заказам
    customer_volume = {}
    for o in completed_orders:
        name = o["customer"]
        if name in customer_volume:
            customer_volume[name] += o["cost"]
        else:
            customer_volume[name] = o["cost"]

    best_customers = []
    max_volume = 0.0
    if customer_volume:
        max_volume = max(customer_volume.values())
        for cust, vol in customer_volume.items():
            if abs(vol - max_volume) < 1e-5:
                best_customers.append(cust)

    return {
        "total_count": total_orders,
        "completed_count": len(completed_orders),
        "cancelled_count": len(cancelled_orders),
        "total_cost": round(total_cost, 2),
        "revenue": round(revenue, 2),
        "avg_cost": avg_cost,
        "most_expensive": most_expensive,
        "best_customers": best_customers if best_customers else ["Нет выполненных заказов"],
        "max_volume": round(max_volume, 2)
    }

def calculate_category_statistics(orders):
    """Статистика объемов продаж в разрезе категорий товаров."""
    stats = {}
    for o in orders:
        cat = o["category"]
        if cat not in stats:
            stats[cat] = {"count": 0, "total_units": 0, "total_cost": 0.0, "completed_cost": 0.0}
        stats[cat]["count"] += 1
        stats[cat]["total_units"] += o["quantity"]
        stats[cat]["total_cost"] += o["cost"]
        if o["status"] == "выполнен":
            stats[cat]["completed_cost"] += o["cost"]

    for cat in stats:
        stats[cat]["avg_cost"] = round(stats[cat]["total_cost"] / stats[cat]["count"], 2)
        stats[cat]["total_cost"] = round(stats[cat]["total_cost"], 2)
        stats[cat]["completed_cost"] = round(stats[cat]["completed_cost"], 2)
    return stats

def calculate_status_statistics(orders):
    """Сбор статистики по количеству каждого из статусов."""
    stats = {}
    for status in VALID_STATUSES:
        stats[status] = 0
    for o in orders:
        if o["status"] in stats:
            stats[o["status"]] += 1
    return stats

def format_order_row(o):
    """Унифицированное форматирование одной записи заказа для вывода."""
    return (f"Заказ #{o['id']} | Покупатель: {o['customer']} | "
            f"Категория: {o['category']} | Кол-во: {o['quantity']} | "
            f"Цена: {o['price']} | Сумма: {o['cost']} | Статус: {o['status']} | "
            f"Категория цены: {o['cost_category']}")
def save_report_to_file(file_path, orders, errors):
    """Запись итоговой аналитики в файл отчета orders_report.txt."""
    with open(file_path, mode='w', encoding='utf-8') as f:
        f.write(f"1. Количество корректных записей: {len(orders)}\n")
        f.write(f"2. Количество некорректных записей: {len(errors)}\n\n")
        
        f.write("3. Перечень уникальных категорий:\n")
        for cat in get_unique_categories(orders):
            f.write(f" - {cat}\n")
            
        f.write("\n4. Заказы по убыванию стоимости:\n")
        for o in sort_orders_by_cost(orders):
            f.write(f" {format_order_row(o)}\n")
            
        f.write("\n5. Перечень крупных заказов:\n")
        for o in get_large_orders(orders):
            f.write(f" {format_order_row(o)}\n")
            
        f.write("\n6. Общие показатели:\n")
        m = calculate_general_metrics(orders)
        if m:
            f.write(f" Всего заказов: {m['total_count']}\n")
            f.write(f" Выполненных: {m['completed_count']}\n")
            f.write(f" Отмененных: {m['cancelled_count']}\n")
            f.write(f" Общая стоимость: {m['total_cost']}\n")
            f.write(f" Выручка: {m['revenue']}\n")
            f.write(f" Средний чек: {m['avg_cost']}\n")
            f.write(f" Самый дорогой: #{m['most_expensive']['id']} ({m['most_expensive']['cost']} руб.)\n")
            f.write(f" Топ-покупатели: {', '.join(m['best_customers'])} (Сумма: {m['max_volume']} руб.)\n")
            
        f.write("\n7. Статистика по категориям:\n")
        for cat, s in calculate_category_statistics(orders).items():
            f.write(f" {cat}: заказов {s['count']}, единиц {s['total_units']}, "
                    f"общая стоимость {s['total_cost']}, выполненная стоимость {s['completed_cost']}, "
                    f"средний чек {s['avg_cost']}\n")
            
        f.write("\n8. Статистика по статусам:\n")
        for stat, count in calculate_status_statistics(orders).items():
            f.write(f" {stat}: {count} шт.\n")
            
        f.write("\n9. Список ошибок входных данных:\n")
        for err in errors:
            f.write(f" {err}\n")

def run_console_menu(orders, errors):
    """Интерактивное консольное меню управления программой."""
    while True:
        print("\n=== МЕНЮ ===")
        print("1. Показать все заказы")
        print("2. Показать заказы по убыванию стоимости")
        print("3. Показать заказы по категориям")
        print("4. Найти заказы по статусу")
        print("5. Найти заказы по категории")
        print("6. Найти заказы покупателя")
        print("7. Показать крупные заказы")
        print("8. Показать статистику")
        print("9. Сохранить отчёт")
        print("0. Завершить программу")
        
        choice = input("Пункт: ").strip()
        if choice == "1":
            for o in orders: print(format_order_row(o))
        elif choice == "2":
            for o in sort_orders_by_cost(orders): print(format_order_row(o))
        elif choice == "3":
            for o in sort_orders_by_category_and_name(orders): print(format_order_row(o))
        elif choice == "4":
            st = input("Введите статус: ")
            res = filter_by_status(orders, st)
            if not res: print("Заказов со статусным фильтром не обнаружено.")
            for o in res: print(format_order_row(o))
        elif choice == "5":
            cat = input("Введите категорию: ")
            res = filter_by_category(orders, cat)
            if not res: print("Заказов в данной категории не найдено.")
            for o in res: print(format_order_row(o))
        elif choice == "6":
            name = input("Введите имя покупателя (часть): ")
            res = search_by_customer_name(orders, name)
            if not res: print("Покупатель с таким именем не найден.")
            for o in res: print(format_order_row(o))
        elif choice == "7":
            res = get_large_orders(orders)
            if not res: print("Крупных заказов (>= 5000) нет.")
            for o in res: print(format_order_row(o))
        elif choice == "8":
            m = calculate_general_metrics(orders)
            if m:
                print("\n[Общие показатели]")
                print(f"Всего: {m['total_count']} | Выручка: {m['revenue']} | Ср. чек: {m['avg_cost']}")
                print(f"Самый дорогой: #{m['most_expensive']['id']} на сумму {m['most_expensive']['cost']}")
                print(f"Лучший покупатель: {', '.join(m['best_customers'])}")
                print("\n[Статистика по категориям]")
                for cat, s in calculate_category_statistics(orders).items():
                    print(f" {cat}: заказов {s['count']}, сумма {s['total_cost']}")
                print("\n[Статистика по статусам]")
                for stat, count in calculate_status_statistics(orders).items():
                    print(f" {stat}: {count} шт.")
        elif choice == "9":
            save_report_to_file("orders_report.txt", orders, errors)
            print("Успешно экспортировано! Проверьте файл 'orders_report.txt'.")
        elif choice == "0":
            print("Программа успешно завершена.")
            break
        else:
            print("Неизвестный пункт меню. Повторите ввод.")

def run_automatic_tests():
    """Обязательные автоматические проверки assert перед запуском (требование ТЗ)."""
    assert get_cost_category(999.99) == "Малый", "Ошибка assert: 999.99 должен быть Малым"
    assert get_cost_category(1000.0) == "Средний", "Ошибка assert: 1000.0 должен быть Средним"
    assert get_cost_category(5000.0) == "Крупный", "Ошибка assert: 5000.0 должен быть Крупным"
    
    mock_data = [
        {"id": 1, "customer": "Алексей", "category": "Книги", "quantity": 2, "price": 100.0, "status": "выполнен", "cost": 200.0, "cost_category": "Малый"},
        {"id": 2, "customer": "Иван", "category": "Электроника", "quantity": 1, "price": 6000.0, "status": "новый", "cost": 6000.0, "cost_category": "Крупный"}
    ]
    assert len(get_large_orders(mock_data)) == 1, "Ошибка assert в фильтрации крупных заказов"
    assert calculate_general_metrics(mock_data)["revenue"] == 200.0, "Ошибка assert в расчете выручки"
    assert len(search_by_customer_name(mock_data, "алекс")) == 1, "Ошибка assert в поиске имени"
    
    print("Все встроенные тесты программы (assert) успешно пройдены!")

# Главная точка входа в программу
if __name__ == '__main__':
    run_automatic_tests()
    
    try:
        orders_list, errors_list = load_orders("orders.txt")
        print(f"Успешных заказов: {len(orders_list)}, Ошибок: {len(errors_list)}")
        run_console_menu(orders_list, errors_list)
        
    except FileNotFoundError as ex:
        print(f"Критическая ошибка: {ex}")
        print("Пожалуйста, создайте файл 'orders.txt' рядом со скриптом и перезапустите его.")
