from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Returns the value of the dictionary for the given key."""
    return dictionary.get(key)
