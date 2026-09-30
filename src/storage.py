"""
Модуль для сохранения и чтения данных из файлов.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import List
from .models import Aeroplane


class BaseStorage(ABC):
    """Абстрактный класс для хранилища."""

    @abstractmethod
    def save_all(self, aeroplanes: List[Aeroplane]) -> None:
        pass

    @abstractmethod
    def load_all(self) -> List[Aeroplane]:
        pass


class JSONStorage(BaseStorage):
    """Сохранение данных в JSON файл."""

    def __init__(self, filename: str = "aeroplanes.json"):
        self.filename = filename

    def save_all(self, aeroplanes: List[Aeroplane]) -> None:
        """Сохраняем список объектов как список словарей."""
        data_to_save = []
        for plane in aeroplanes:
            data_to_save.append(
                {
                    "callsign": plane.callsign,
                    "country": plane.country,
                    "velocity": plane.velocity,
                    "altitude": plane.altitude,
                }
            )

        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data_to_save, f, indent=4, ensure_ascii=False)

    def load_all(self) -> List[Aeroplane]:
        """Читаем файл и превращаем словари обратно в объекты Aeroplane."""
        if not os.path.exists(self.filename):
            return []

        with open(self.filename, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                return []  # Если файл пустой или битый, возвращаем пустой список

        aeroplanes_list = []
        for item in data:
            plane = Aeroplane(
                callsign=item["callsign"],
                country=item["country"],
                velocity=item["velocity"],
                altitude=item["altitude"],
            )
            aeroplanes_list.append(plane)

        return aeroplanes_list
