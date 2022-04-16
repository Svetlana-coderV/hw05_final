import datetime
from typing import Dict, Any


def year(request: Any) -> Dict[str, int]:
    """Добавляет в footer переменную с текущим годом."""
    date: datetime = datetime.datetime.today()
    return {
        'year': date.year
    }
