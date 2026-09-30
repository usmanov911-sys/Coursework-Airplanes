"""
Главный файл программы. Здесь происходит взаимодействие с пользователем.
"""

import sys
from typing import List
from .models import Aeroplane
from .api_client import FlightAPIClient
from .storage import JSONStorage


def get_top_n_by_altitude(aeroplanes: List[Aeroplane], n: int) -> List[Aeroplane]:
    """Возвращает топ N самолетов по высоте (от большей к меньшей)."""
    # sorted сортирует по возрастанию, reverse=True делает по убыванию
    sorted_planes = sorted(
        aeroplanes, key=lambda x: (x.altitude, x.velocity), reverse=True
    )
    return sorted_planes[:n]


def filter_by_country(
    aeroplanes: List[Aeroplane], countries: List[str]
) -> List[Aeroplane]:
    """Фильтрует самолеты, оставляя только те, что из указанных стран."""
    # Приводим введенные страны к нижнему регистру для удобного сравнения
    countries_lower = [c.lower() for c in countries]
    result = []
    for plane in aeroplanes:
        if plane.country.lower() in countries_lower:
            result.append(plane)
    return result


def user_interaction() -> None:
    """Основной цикл программы."""
    print("=== Привет! Это программа для отслеживания самолетов ===")

    api_client = FlightAPIClient()
    storage = JSONStorage("flights_data.json")

    while True:
        print("\n--- Меню ---")
        print("1. Загрузить данные о самолетах для новой страны")
        print("2. Показать топ N самолетов по высоте")
        print("3. Отфильтровать по стране регистрации")
        print("4. Выход")

        choice = input("Выберите действие (1-4): ").strip()

        if choice == "1":
            country = input(
                "Введите название страны (на английском, например, Spain): "
            ).strip()
            if not country:
                print("Ошибка: название страны не может быть пустым.")
                continue

            try:
                print("Загружаю данные... (подождите)")
                raw_data = api_client.get_data(country)
                aeroplanes = Aeroplane.from_api_data(raw_data)

                if not aeroplanes:
                    print("Самолетов в этом регионе не найдено.")
                else:
                    storage.save_all(aeroplanes)
                    print(f"Успешно! Сохранено {len(aeroplanes)} самолетов в файл.")
            except ValueError as e:
                print(f"Ошибка данных: {e}")
            except ConnectionError as e:
                print(f"Ошибка сети: {e}")
            except Exception as e:
                print(f"Произошла непредвиденная ошибка: {e}")

        elif choice == "2":
            aeroplanes = storage.load_all()
            if not aeroplanes:
                print("Нет данных. Сначала загрузите их в пункте 1.")
                continue

            try:
                n = int(input("Сколько самолетов показать в топе? "))
                if n <= 0:
                    print("Число должно быть больше 0.")
                    continue

                top_planes = get_top_n_by_altitude(aeroplanes, n)
                print(f"\n--- Топ {n} самолетов по высоте ---")
                for p in top_planes:
                    print(p)
            except ValueError:
                print("Ошибка: нужно ввести целое число.")

        elif choice == "3":
            aeroplanes = storage.load_all()
            if not aeroplanes:
                print("Нет данных. Сначала загрузите их в пункте 1.")
                continue

            countries_input = input(
                "Введите страны для поиска через пробел (например, United States France): "
            ).strip()
            if not countries_input:
                print("Ошибка: список стран не может быть пустым.")
                continue

            countries_list = countries_input.split()
            filtered = filter_by_country(aeroplanes, countries_list)

            print(f"\n--- Найдено {len(filtered)} самолетов ---")
            for p in filtered[:20]:  # Ограничим вывод, чтобы не спамить в консоль
                print(p)
            if len(filtered) > 20:
                print("... и еще", len(filtered) - 20, "самолетов.")

        elif choice == "4":
            print("До свидания!")
            sys.exit(0)
        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":
    user_interaction()
