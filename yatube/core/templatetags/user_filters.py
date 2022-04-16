from typing import Any

from django import template
from django.forms import BoundField
from django.utils.safestring import SafeText

register = template.Library()


@register.filter
def addclass(field: BoundField, css: SafeText) -> Any:
    """Фильтр, который дает возможность указывать css-класс в шаблоне"""
    return field.as_widget(attrs={'class': css})
