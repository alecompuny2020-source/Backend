from rest_framework.renderers import JSONRenderer
from django.utils.translation import gettext_lazy as _
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework_guardian.filters import ObjectPermissionsFilter


class GeneralEntepriseJSONRenderer(JSONRenderer):
    """ A custom render for consistent API response through out the Enterprise"""
    def render(self, data, accepted_media_type=None, renderer_context=None):

        if isinstance(data, dict) and "error" in data:
            return super().render(data, accepted_media_type, renderer_context)

        if data is None:
            return super().render({
                "success": True,
                "message": _("Action performed successfully"),
                "data": None
            }, accepted_media_type, renderer_context)

        standardized_data = {
            "success": True,
            "message": _("Request processed successfully"),
            "data": data,
        }

        # Extracts custom messages or data from the view if provided
        if isinstance(data, dict):
            if "message" in data:
                standardized_data["message"] = data.pop("message")
            if "data" in data and len(data) == 1: # If 'data' was the only other key
                standardized_data["data"] = data.pop("data")

        return super().render(standardized_data, accepted_media_type, renderer_context)


class GenericEnteprisePaginator(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
