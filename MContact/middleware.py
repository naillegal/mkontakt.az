from django.utils import translation
from django.conf import settings

SUPPORTED = {c for c, _ in settings.LANGUAGES}

class CustomLocaleMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        override = path.startswith('/api/') and not path.startswith('/api/swagger')
        lang = None
        if override:
            header = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
            if header:
                raw = header.split(',')[0].strip().lower()
                lang = raw.split('-')[0]
                if lang not in SUPPORTED:
                    lang = None

        if not lang:
            return self.get_response(request)

        with translation.override(lang):
            response = self.get_response(request)
        response.headers['Content-Language'] = lang
        return response
