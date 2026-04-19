from django.shortcuts import render
from rest_framework_guardian.filters import ObjectPermissionsFilter
from rest_framework import viewsets, permissions, filters, status
from helpers.permissions import CustomFarmPermissions
from utils.renderers import GenericPaginator
from .models import Supplier
from .serializers import SupplierSerializer

# Create your views here.


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['name', 'location', 'is_active']
    search_fields = [
        'name', 'contact', 'location', 'is_active', 'created_by',
        'updated_by'
    ]
    ordering_fields = ["name", "contact", "is_active"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Supplier created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Supplier was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Supplier was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)
