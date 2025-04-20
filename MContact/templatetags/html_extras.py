import html
from django import template

register = template.Library()

@register.filter(name='html_unescape')
def html_unescape(value):
    return html.unescape(value)
