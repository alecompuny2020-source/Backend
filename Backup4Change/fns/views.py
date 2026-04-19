from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework_guardian.filters import ObjectPermissionsFilter
from rest_framework.response import Response
from helpers.permissions import GuardianObjectPermissions
from .models import (
    FeedType, FeedInventory, FeedConsumption
    )
from .serializers import (
    FeedTypeSerializer, FeedInventorySerializer, FeedConsumptionSerializer
    )

# Create your views here.

class FeedTypeViewSet(viewsets.ModelViewSet):
    queryset = FeedType.objects.all()
    serializer_class = FeedTypeSerializer
    permission_classes = [GuardianObjectPermissions]
    filter_backends = [ObjectPermissionsFilter]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Record created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Record was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Record was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)


class FeedInventoryViewSet(viewsets.ModelViewSet):
    queryset = FeedInventory.objects.all()
    serializer_class = FeedInventorySerializer
    permission_classes = [GuardianObjectPermissions]
    filter_backends = [ObjectPermissionsFilter]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Record created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Record was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Record was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)


class FeedConsumptionViewSet(viewsets.ModelViewSet):
    queryset = FeedConsumption.objects.all()
    serializer_class = FeedConsumptionSerializer
    permission_classes = [GuardianObjectPermissions]
    filter_backends = [ObjectPermissionsFilter]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Record created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Record was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Record was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)
