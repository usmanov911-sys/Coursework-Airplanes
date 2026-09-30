"""
Модуль для запросов к внешним API.
Используем библиотеку requests.
"""

import requests
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAPIClient(ABC):
    """Абстрактный класс для клиентов API."""

    @abstractmethod
    def get_data(self, query: str) -> Dict[str, Any]:
        pass


class FlightAPIClient(BaseAPIClient):
    """Клиент для получения данных о самолетах через Nominatim и OpenSky."""

    def __init__(self):
        # Используем Session, чтобы не создавать новое соединение каждый раз
        self.session = requests.Session()
        # Указываем User-Agent, иначе Nominatim может заблокировать запрос
        self.session.headers.update({"User-Agent": "SkillboxCourseProject/1.0"})

    def _get_country_bbox(self, country_name: str) -> dict:
        """Получаем координаты границ страны (bounding box) через Nominatim."""
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": country_name, "format": "json", "limit": 1}

        response = self.session.get(url, params=params)
        # Если произошла ошибка сети, выбросим исключение
        response.raise_for_status()
        data = response.json()

        if not data:
            raise ValueError(f"Страна '{country_name}' не найдена в базе.")

        # boundingbox приходит как список: [юг, север, запад, восток]
        bbox = data[0]["boundingbox"]
        return {
            "lamin": float(bbox[0]),  # минимальная широта
            "lamax": float(bbox[1]),  # максимальная широта
            "lomin": float(bbox[2]),  # минимальная долгота
            "lomax": float(bbox[3]),  # максимальная долгота
        }

    def get_data(self, country_name: str) -> Dict[str, Any]:
        """Основной метод: получает координаты страны и запрашивает самолеты."""
        try:
            # Сначала узнаем границы страны
            bbox = self._get_country_bbox(country_name)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ошибка сети при запросе координат: {e}")
        except ValueError as e:
            raise e  # Пробрасываем ошибку, если страна не найдена

        # Теперь запрашиваем самолеты в этих границах
        url = "https://opensky-network.org/api/states/all"
        params = {
            "lamin": bbox["lamin"],
            "lamax": bbox["lamax"],
            "lomin": bbox["lomin"],
            "lomax": bbox["lomax"],
        }

        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Ошибка сети при запросе самолетов: {e}")
