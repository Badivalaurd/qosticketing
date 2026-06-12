from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Dict/list lookup in templates: {{ my_dict|get_item:key }}"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    try:
        return dictionary[key]
    except (IndexError, KeyError, TypeError):
        return None
