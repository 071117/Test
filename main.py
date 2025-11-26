from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException
)
from selenium.webdriver.chrome.options import Options
import time
import random
import re
from urllib.parse import urlparse

ALLOWED_DOMAINS = ["ria.ru", "lenta.ru", "tass.ru"]

def validate_url_client_side(url: str) -> bool:
    """Клиентская валидация: проверяет ТОЛЬКО формат URL (без доступа к интернету)"""
    try:
        result = urlparse(url)
        if not all([result.scheme in ('http', 'https'), result.netloc]):
            print("Ошибка: Некорректный формат URL (требуется http:// или https:// + домен)")
            return False
        return True
    except Exception:
        print("Ошибка: Неверный формат ссылки")
        return False


def validate_page_content(driver) -> bool:
    """Серверная валидация: проверяет домен И наличие элементов после загрузки"""
    try:
        # 1. Проверяем домен
        current_domain = urlparse(driver.current_url).netloc.lower()
        current_domain = re.sub(r'^www\.', '', current_domain)  # Убираем www.

        if current_domain not in ALLOWED_DOMAINS:
            print(f"Ошибка: Домен '{current_domain}' не входит в список разрешенных для парсинга")
            return False

        # 2. Проверяем наличие элементов (селекторы для всех доменов)
        required_selectors = {
            "ria.ru": ".cell-list__item-title",
            "lenta.ru": ".item a.title",  # Пример для lenta.ru (нужно уточнить реальный селектор)
            "tass.ru": ".news-list__item-title"  # Пример для tass.ru
        }

        selector = required_selectors.get(current_domain)
        if not selector:
            print(f"Ошибка: Нет селектора для домена {current_domain}")
            return False

        driver.find_element(By.CSS_SELECTOR, selector)
        return True

    except Exception as e:
        print(f"Ошибка валидации содержимого: {str(e)}")
        return False

def init_driver() -> webdriver.Chrome:
    """Настройка драйвера: headless-режим, подмена user-agent, отключение детекции автоматизации."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.navigator.chrome = {runtime: {}, app: {}};
    """)
    return driver

def scroll_to_load(driver: webdriver.Chrome) -> None:
    """Эмуляция человеческой прокрутки для подгрузки контента"""
    scroll_pause = 0.8
    screen_height = driver.execute_script("return window.innerHeight")

    for _ in range(3):  # 3 этапа прокрутки
        driver.execute_script(f"window.scrollBy(0, {screen_height});")
        time.sleep(scroll_pause + random.uniform(0.2, 0.5))
        scroll_pause += 0.3  # Увеличиваем паузу для естественности


def extract_headlines(driver: webdriver.Chrome) -> list[str]:
    """Извлечение первых 5 заголовков с учетом домена"""
    current_domain = urlparse(driver.current_url).netloc.lower()
    current_domain = re.sub(r'^www\.', '', current_domain)

    # Селекторы для каждого домена
    selectors = {
        "ria.ru": ".cell-list__item-title",
        "lenta.ru": ".item a.title",  # Пример, замените на реальный
        "tass.ru": ".news-list__item-title"  # Пример
    }

    selector = selectors.get(current_domain)
    if not selector:
        print(f"Ошибка: Нет селектора для извлечения заголовков с {current_domain}")
        return []

    headlines = []
    attempts = 0
    while attempts < 3 and len(headlines) < 5:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                if len(headlines) >= 5:
                    break
                try:
                    text = el.text.strip()
                    if text and text not in headlines:
                        headlines.append(text)
                except StaleElementReferenceException:
                    continue
            break
        except (TimeoutException, NoSuchElementException):
            attempts += 1
            time.sleep(1)
    return headlines[:5]

if __name__ == "__main__":
    while True:  # Основной цикл для всего процесса
        # 1. Запрашиваем URL
        target_url = input("Введите URL для парсинга: ").strip()

        # 2. Клиентская валидация формата
        if not validate_url_client_side(target_url):
            print("Попробуйте снова.\n")
            continue

        # 3. Проверяем домен ДО создания браузера
        parsed_url = urlparse(target_url)
        current_domain = parsed_url.netloc.lower().replace('www.', '')

        if current_domain not in ALLOWED_DOMAINS:
            print(f"Ошибка: Домен '{current_domain}' не поддерживается для парсинга")
            print("Доступные домены: ria.ru, lenta.ru, tass.ru\n")
            continue  # Возвращаемся к вводу URL

        # 4. Создаем браузер и загружаем страницу
        driver = init_driver()
        try:
            driver.set_page_load_timeout(15)
            try:
                driver.get(target_url)
                time.sleep(2)
            except TimeoutException:
                print(f"Ошибка: Превышено время ожидания загрузки страницы {target_url}")
                driver.quit()
                continue

            # 5. Валидация содержимого страницы
            if not validate_page_content(driver):
                print("Парсинг отменён: не найдены элементы для извлечения данных\n")
                driver.quit()
                continue

            # 6. Успешная валидация - извлекаем данные
            scroll_to_load(driver)
            time.sleep(2)
            headlines = extract_headlines(driver)

            print("\nПолученные заголовки:")
            for i, title in enumerate(headlines, 1):
                print(f"{i}. {title}")

            # 7. Успешное завершение после получения данных
            driver.quit()
            break

        except Exception as e:
            print(f"Критическая ошибка: {str(e)}")
            driver.quit()
            continue