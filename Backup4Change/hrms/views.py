from django.shortcuts import render
from .models import Department, NextOfKin, UserIdentity
from .serializers import (DepartmentSerializer, NextOfKinSerializer, UserIdentitySerializer)
from rest_framework import viewsets, permissions, status
from rest_framework_guardian.filters import ObjectPermissionsFilter
from rest_framework.response import Response
from helpers.permissions import GuardianObjectPermissions

# Create your views here.

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [GuardianObjectPermissions]
    filter_backends = [ObjectPermissionsFilter]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Department created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Department was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Department was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)


class NextOfKinsViewSet(viewsets.ModelViewSet):
    queryset = NextOfKin.objects.all()
    serializer_class = NextOfKinSerializer
    permission_classes = [GuardianObjectPermissions]
    filter_backends = [ObjectPermissionsFilter]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Next of kin added successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Next of kin was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Next of kin was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)


class UserIdentityViewSet(viewsets.ModelViewSet):
    queryset = UserIdentity.objects.all()
    serializer_class = UserIdentitySerializer
    permission_classes = [GuardianObjectPermissions]
    filter_backends = [ObjectPermissionsFilter]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        id_type = serializer.validated_data['identity_type']
        self.perform_create(serializer)
        message = f"{id_type.upper()} added successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        id_type = serializer.validated_data['identity_type']
        self.perform_update(serializer)
        message = f"{id_type.upper()} was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        id_type = instance.identity_type
        self.perform_destroy(instance)
        message = f"{id_type.upper()} was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)
