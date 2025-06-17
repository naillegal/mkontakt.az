from django import template
from django.urls import translate_url

register = template.Library()

@register.simple_tag(takes_context=True)
def lang_url(context, lang_code):
    request = context["request"]
    return translate_url(request.get_full_path(), lang_code)
