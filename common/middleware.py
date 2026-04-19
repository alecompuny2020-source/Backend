from django.utils import translation
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class EnterpriseUserPreferenceMiddleware(MiddlewareMixin):
    """
    Middleware to globally apply user-specific localization settings.

    It extracts 'preferred_language' and 'preferred_currency' from the
    UserPreference JSONField and attaches them to the request object
    for use in views, serializers, and templates.
    """

    def process_request(self, request):
        request.CURRENCY = getattr(settings, 'DEFAULT_CURRENCY', 'TZS')

        if request.user.is_authenticated:
            user_pref_obj = getattr(request.user, 'preferences', None)

            if user_pref_obj and user_pref_obj.preferences:
                prefs = user_pref_obj.preferences

                # Handle Language
                user_lang = prefs.get('preferred_language')
                if user_lang:
                    translation.activate(user_lang)
                    request.LANGUAGE_CODE = translation.get_language()

                # Handle Currency
                user_curr = prefs.get('preferred_currency')
                if user_curr:
                    request.CURRENCY = user_curr
