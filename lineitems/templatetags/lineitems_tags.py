from django import template

register = template.Library()


@register.simple_tag
def search_url():
    return "?page=1&doctype={{doctype}}&fund={{fund}}&costcenter={{costcenter}}"
