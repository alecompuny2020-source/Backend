from django.utils.translation import gettext_lazy as _
from rest_framework import filters, permissions, status, viewsets
from rest_framework.response import Response

from common.constants import current_time
from common.pagination import GenericEnteprisePaginator


class BaseEnterpriseViewSet(viewsets.ModelViewSet):
    """
    A base ViewSet to handle shared configuration and consistent success or error messages.
    """

    pagination_class = GenericEnteprisePaginator
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering = ["-id"]

    def get_permissions(self):
        """
        Default baseline permissions for standard enterprise views.
        Public can read, authenticated users can write.
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_model_name(self):
        return self.queryset.model._meta.verbose_name.title()

    def get_success_message(self):
        model_name = self.get_model_name()

        messages = {
            "create": f"{model_name} created successfully",
            "update": f"{model_name} was updated successfully",
            "partial_update": f"{model_name} was updated successfully",
            "destroy": f"{model_name} was deleted successfully",
        }
        return messages.get(self.action, "Action successful")

    def perform_create(self, serializer):
        if hasattr(serializer.Meta.model, "created_by"):
            serializer.save(created_by=self.request.user)
        else:
            serializer.save()

    def perform_update(self, serializer):
        model = serializer.Meta.model
        save_kwargs = {}

        if hasattr(model, "updated_by") and self.request.user.is_authenticated:
            save_kwargs["updated_by"] = self.request.user

        if hasattr(model, "updated_on"):
            save_kwargs["updated_on"] = current_time

        serializer.save(**save_kwargs)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response(
            {"message": self.get_success_message()}, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response(
            {"message": self.get_success_message()}, status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return Response(
            {"message": self.get_success_message()}, status=status.HTTP_200_OK
        )
