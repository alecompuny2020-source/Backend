from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from core.serializers import (UserPersonalInfoSerializer, UserContactInfoSerializer
, ProfilePictureSerializer, UserAddressSerializer, UserPreferenceSerializer)
from core.models import User

class UserProfileViewSet(viewsets.GenericViewSet):
    """
    Unified ViewSet for granular user profile management.
    Uses a centralized dispatcher to handle CRUD operations across different entities.
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()


    def _handle_action(self, instance_or_queryset, serializer_class, request,
                       many=False, success_msg="Operation successful"):
        """
        Generic action dispatcher to handle GET, POST, PUT, PATCH, DELETE
        for granular profile sections.
        """
        method = request.method.lower()

        if method == "get":
            serializer = serializer_class(instance_or_queryset, many=many)
            return Response(serializer.data)

        if method == "post":
            if instance_or_queryset and not many:
                return Response({"error": "Resource already exists."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(user=request.user)
            return Response({"detail": success_msg}, status=status.HTTP_201_CREATED)

        if method in ["put", "patch"]:
            obj = instance_or_queryset
            if many:
                obj_id = request.data.get("id")
                obj = instance_or_queryset.filter(id=obj_id).first()
                if not obj:
                    return Response({"error": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

            if not obj:
                 return Response({"error": "Resource not found."}, status=status.HTTP_404_NOT_FOUND)

            serializer = serializer_class(obj, data=request.data, partial=(method == "patch"))
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"detail": success_msg})

        if method == "delete":
            obj = instance_or_queryset
            if many:
                obj_id = request.data.get("id")
                obj = instance_or_queryset.filter(id=obj_id).first()

            if not obj:
                return Response({"error": "Nothing to delete."}, status=status.HTTP_404_NOT_FOUND)

            if hasattr(obj, 'profile_picture') and hasattr(obj.profile_picture, 'delete'):
                obj.profile_picture.delete(save=False)
                obj.profile_picture = None
                obj.save()
            else:
                obj.delete()

            return Response({"detail": "Deleted successfully."})


    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def personal_info(self, request):
        """Manage core personal details."""
        return self._handle_action(request.user, UserPersonalInfoSerializer, request)

    @action(detail=False, methods=["get", "put", "patch"])
    def contact_info(self, request):
        """Manage email and phone."""
        return self._handle_action(request.user, UserContactInfoSerializer, request)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def profile_picture(self, request):
        """Manage profile picture file."""
        return self._handle_action(request.user, ProfilePictureSerializer, request)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def addresses(self, request):
        """Manage user addresses (Collection)."""
        return self._handle_action(request.user.addresses.all(), UserAddressSerializer, request, many=True)

    @action(detail=False, methods=["get", "post", "put", "patch", "delete"])
    def preferences(self, request):
        """ Manage user system preferences."""
        pref = getattr(request.user, 'preferences', None)
        return self._handle_action(pref, UserPreferenceSerializer, request)
