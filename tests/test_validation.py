import pytest
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для GitHub Actions
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import validate_url_client_side

@pytest.mark.parametrize("url, expected", [
    ("https://ria.ru", True),
    ("http://lenta.ru", True),
    ("https://tass.ru/news", True),
    ("ftp://invalid.ru", False),
    ("not_a_url", False),
    ("https://www.ria.ru", True),
])
def test_url_validation(url, expected):
    assert validate_url_client_side(url) == expected