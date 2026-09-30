import pytest
import json
import os
from unittest.mock import patch, MagicMock
from src.models import Aeroplane
from src.storage import JSONStorage
from src.api_client import FlightAPIClient
from src.main import get_top_n_by_altitude, filter_by_country


class TestAeroplaneModel:
    """Тесты для класса самолета."""

    def test_create_aeroplane(self):
        """Проверяем, что объект создается с правильными данными."""
        plane = Aeroplane("SU100", "Russia", 250.5, 10000.0)
        assert plane.callsign == "SU100"
        assert plane.country == "Russia"
        assert plane.velocity == 250.5
        assert plane.altitude == 10000.0

    def test_none_values_become_zero(self):
        """Если данных о скорости нет, должно быть 0.0."""
        plane = Aeroplane("TEST", "USA", None, None)
        assert plane.velocity == 0.0
        assert plane.altitude == 0.0

    def test_comparison(self):
        """Проверяем, что самолеты корректно сравниваются по высоте."""
        p1 = Aeroplane("A", "US", 100, 5000)
        p2 = Aeroplane("B", "US", 100, 10000)

        # p2 выше, чем p1, значит p1 < p2
        assert p1 < p2
        assert p2 > p1

    def test_from_api_data(self):
        """Тестируем создание списка самолетов из данных API."""
        # Имитируем ответ от OpenSky API
        mock_response = {
            "states": [
                ["icao1", "CALL1", "Country1", None, None, None, None, 5000.0, False, 150.0, None, None, None, None,
                 None, False, 0],
                ["icao2", "CALL2", "Country2", None, None, None, None, None, False, None, None, None, None, None, None,
                 False, 0],
                ["icao3", None, None, None, None, None, None, 3000.0, False, 200.0, None, None, None, None, None, False,
                 0]
            ]
        }

        planes = Aeroplane.from_api_data(mock_response)

        assert len(planes) == 3
        assert planes[0].callsign == "CALL1"
        assert planes[0].country == "Country1"
        assert planes[0].altitude == 5000.0
        assert planes[0].velocity == 150.0

        # Второй самолет имеет None для altitude, должно стать 0.0
        assert planes[1].altitude == 0.0
        assert planes[1].velocity == 0.0

        # Третий самолет имеет None для callsign и country
        assert planes[2].callsign == "UNKNOWN"
        assert planes[2].country == "Unknown Country"


class TestJSONStorage:
    """Тесты для сохранения в JSON."""

    def test_save_and_load(self, tmp_path):
        """Проверяем, что данные сохраняются и читаются обратно."""
        file_path = tmp_path / "test.json"
        storage = JSONStorage(str(file_path))

        planes = [
            Aeroplane("TEST1", "US", 100, 1000),
            Aeroplane("TEST2", "RU", 200, 2000)
        ]

        # Сохраняем
        storage.save_all(planes)

        # Загружаем и проверяем
        loaded = storage.load_all()
        assert len(loaded) == 2
        assert loaded[0].callsign == "TEST1"
        assert loaded[1].country == "RU"

    def test_load_nonexistent_file(self, tmp_path):
        """Если файла нет, должен вернуться пустой список."""
        file_path = tmp_path / "nonexistent.json"
        storage = JSONStorage(str(file_path))

        loaded = storage.load_all()
        assert loaded == []


class TestFlightAPIClient:
    """Тесты для клиента API с мокированием запросов."""

    @patch('src.api_client.requests.Session.get')
    def test_get_data_success(self, mock_get):
        """Тестируем успешный запрос данных."""
        # Мокаем два последовательных вызова: сначала Nominatim, потом OpenSky
        mock_get.side_effect = [
            # Ответ от Nominatim (координаты страны)
            MagicMock(
                json=lambda: [{"boundingbox": ["40.0", "50.0", "-10.0", "10.0"]}],
                status_code=200,
                raise_for_status=lambda: None
            ),
            # Ответ от OpenSky (самолеты)
            MagicMock(
                json=lambda: {"states": [["icao", "CALL", "Country", None, None, None, None, 1000, False, 100]]},
                status_code=200,
                raise_for_status=lambda: None
            )
        ]

        client = FlightAPIClient()
        result = client.get_data("Spain")

        assert "states" in result
        assert mock_get.call_count == 2

    @patch('src.api_client.requests.Session.get')
    def test_get_data_country_not_found(self, mock_get):
        """Тестируем ошибку, если страна не найдена."""
        mock_get.return_value = MagicMock(
            json=lambda: [],
            status_code=200,
            raise_for_status=lambda: None
        )

        client = FlightAPIClient()
        with pytest.raises(ValueError, match="Страна 'Nowhere' не найдена"):
            client.get_data("Nowhere")


class TestMainFunctions:
    """Тесты для функций из main.py."""

    def test_get_top_n_by_altitude(self):
        """Тестируем сортировку по высоте."""
        planes = [
            Aeroplane("A", "US", 100, 5000),
            Aeroplane("B", "US", 200, 10000),
            Aeroplane("C", "US", 150, 7000),
            Aeroplane("D", "US", 300, 15000)
        ]

        top_2 = get_top_n_by_altitude(planes, 2)

        assert len(top_2) == 2
        assert top_2[0].callsign == "D"  # Самый высокий
        assert top_2[1].callsign == "B"  # Второй по высоте

    def test_filter_by_country(self):
        """Тестируем фильтрацию по стране."""
        planes = [
            Aeroplane("A", "United States", 100, 5000),
            Aeroplane("B", "France", 200, 10000),
            Aeroplane("C", "Germany", 150, 7000),
            Aeroplane("D", "United States", 300, 15000)
        ]

        filtered = filter_by_country(planes, ["United States", "France"])

        assert len(filtered) == 3
        assert all(p.country in ["United States", "France"] for p in filtered)


class TestUserInteraction:
    """Тесты для консольного интерфейса."""

    @patch('src.main.JSONStorage')
    @patch('src.main.FlightAPIClient')
    def test_user_interaction_exit(self, mock_api_class, mock_storage_class, monkeypatch):
        """Тестируем, что программа корректно завершается при выборе '4'."""
        monkeypatch.setattr('builtins.input', lambda _: '4')

        from src.main import user_interaction
        # sys.exit(0) выбрасывает SystemExit — это нормально, ловим его
        with pytest.raises(SystemExit) as exc_info:
            user_interaction()
        assert exc_info.value.code == 0

    @patch('src.main.JSONStorage')
    @patch('src.main.FlightAPIClient')
    def test_user_interaction_load_data(self, mock_api_class, mock_storage_class, monkeypatch):
        """Тестируем загрузку данных о самолетах."""
        mock_api = MagicMock()
        mock_api.get_data.return_value = {
            "states": [
                ["icao1", "CALL1", "Spain", None, None, None, None, 5000.0, False, 150.0]
            ]
        }
        mock_api_class.return_value = mock_api

        mock_storage = MagicMock()
        mock_storage_class.return_value = mock_storage

        inputs = iter(['1', 'Spain', '4'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        from src.main import user_interaction
        with pytest.raises(SystemExit):
            user_interaction()

        mock_api.get_data.assert_called_once_with("Spain")
        mock_storage.save_all.assert_called_once()

    @patch('src.main.JSONStorage')
    @patch('src.main.FlightAPIClient')
    def test_user_interaction_top_n(self, mock_api_class, mock_storage_class, monkeypatch):
        """Тестируем показ топа N самолетов."""
        mock_storage = MagicMock()
        mock_storage.load_all.return_value = [
            Aeroplane("A", "US", 100, 5000),
            Aeroplane("B", "US", 200, 10000),
            Aeroplane("C", "US", 150, 7000)
        ]
        mock_storage_class.return_value = mock_storage

        inputs = iter(['2', '2', '4'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        from src.main import user_interaction
        with pytest.raises(SystemExit):
            user_interaction()

        mock_storage.load_all.assert_called()

    @patch('src.main.JSONStorage')
    @patch('src.main.FlightAPIClient')
    def test_user_interaction_filter_by_country(self, mock_api_class, mock_storage_class, monkeypatch):
        """Тестируем фильтрацию по стране."""
        mock_storage = MagicMock()
        mock_storage.load_all.return_value = [
            Aeroplane("A", "United States", 100, 5000),
            Aeroplane("B", "France", 200, 10000)
        ]
        mock_storage_class.return_value = mock_storage

        inputs = iter(['3', 'France', '4'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))

        from src.main import user_interaction
        with pytest.raises(SystemExit):
            user_interaction()

        mock_storage.load_all.assert_called()