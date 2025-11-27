from unittest.mock import MagicMock, PropertyMock
from main import extract_headlines


def test_extract_headlines_with_mocks(mocker):
    """Тестирует извлечение заголовков с имитацией Selenium-драйвера"""
    # Создаем мок-объект драйвера
    mock_driver = mocker.MagicMock()

    # КРИТИЧНО: Замокируем current_url как свойство
    type(mock_driver).current_url = PropertyMock(return_value="https://ria.ru")

    # Настраиваем поведение: возвращаем 3 заголовка
    mock_elements = [
        MagicMock(text="Заголовок 1"),
        MagicMock(text="Заголовок 2"),
        MagicMock(text="Заголовок 3")
    ]

    # Настраиваем find_elements
    mock_driver.find_elements.return_value = mock_elements

    # Запускаем тест
    headlines = extract_headlines(mock_driver)

    # Проверяем результат
    assert headlines == ["Заголовок 1", "Заголовок 2", "Заголовок 3"]

    # Проверяем вызов с правильным селектором для RIA.ru
    mock_driver.find_elements.assert_called_once_with(
        "css selector",
        ".cell-list__item-title"
    )
