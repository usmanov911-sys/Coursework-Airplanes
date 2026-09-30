"""
Модуль с классом самолета.
Здесь мы описываем, какие данные есть у самолета и как их сравнивать.
"""


class Aeroplane:
    """Класс для представления самолета в полете."""

    def __init__(self, callsign: str, country: str, velocity: float, altitude: float):
        self.callsign = callsign
        self.country = country

        # Если данных о скорости или высоте нет (None), ставим 0.0,
        # чтобы программа не ломалась при сортировке
        self.velocity = float(velocity) if velocity is not None else 0.0
        self.altitude = float(altitude) if altitude is not None else 0.0

    @classmethod
    def from_api_data(cls, api_response: dict):
        """
        Метод класса для создания списка самолетов из сырых данных API OpenSky.
        Проходимся циклом по ответу и создаем объекты.
        """
        aeroplanes_list = []
        states = api_response.get("states", [])

        for state in states:
            if not state:
                continue

            # По документации OpenSky:
            # индекс 1 - позывной, 2 - страна, 9 - скорость, 7 - высота
            callsign = state[1] if state[1] else "UNKNOWN"
            country = state[2] if state[2] else "Unknown Country"
            velocity = state[9]
            altitude = state[7]

            # Создаем объект и добавляем в список
            plane = cls(callsign, country, velocity, altitude)
            aeroplanes_list.append(plane)

        return aeroplanes_list

    # Магические методы для сравнения (требование задания)
    # Сравниваем сначала по высоте, если она равна - то по скорости
    def __lt__(self, other):
        if self.altitude != other.altitude:
            return self.altitude < other.altitude
        return self.velocity < other.velocity

    def __gt__(self, other):
        if self.altitude != other.altitude:
            return self.altitude > other.altitude
        return self.velocity > other.velocity

    def __str__(self):
        # Делаем красивый вывод для консоли
        return (
            f"Рейс: {self.callsign:<10} | "
            f"Страна: {self.country:<15} | "
            f"Высота: {self.altitude:>7.1f} м | "
            f"Скорость: {self.velocity:>6.1f} м/с"
        )
