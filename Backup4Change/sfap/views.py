from django.shortcuts import render
from rest_framework_guardian.filters import ObjectPermissionsFilter
from rest_framework import viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Q
from .models import (
    Farm, ManagerHistory, FarmShed, Batch, DailyObservation, BreederFlock, Incubator,
    IncubationCycle, HatchRecord, HealthProtocol, MedicalRecord, DiseaseOutbreak,
    DiseaseOutbreak, FarmVehicle, TransportMovement
    )
from .serializers import (
    FarmSerializer, FarmManagerHistorySerializer, FarmShedSerializer, BatchSerializer,
    DailyObservationSerializer, BreederFlockSerializer, IncubatorSerializer,
    IncubationCycleserializer, HatchRecordSerializer, HealthProtocolSerializer,
    MedicalRecordSerializer, DiseaseOutbreakSerializer, FarmVehicleSerializer,
    TransportMovementSerializer
    )
from helpers.permissions import CustomFarmPermissions
from utils.renderers import GenericPaginator


# Create your views here.

class FarmViewSet(viewsets.ModelViewSet):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["region", "is_active", "is_quarantined", "manager"]
    search_fields = ["name", "region", "gps_coordinates", "site_config"]
    ordering_fields = ["name", "region", "manager"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Farm created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Farm was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Farm was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["patch"])
    def assign_manager(self, request):
        """Custom action to assign farm manager"""

        farm_id = request.data.get("id")
        manager_id = request.data.get("manager")

        if not farm_id or not manager_id:
            return Response({"error": "Both farm and manager are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            farm = Farm.objects.get(Q(id=farm_id))
        except Farm.DoesNotExist:
            return Response({"error": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            manager = Employee.objects.get(Q(id=manager_id))

        except Employee.DoesNotExist:
            return Response({"error": "Manager not found."}, status=status.HTTP_404_NOT_FOUND)

        farm.manager = manager
        farm.save()
        message = f"{manager.user.get_full_name()} has been assigned as manager to '{farm.name}' farm."

        return Response({"message": message}, status=status.HTTP_200_OK)

    # @action(detail=False, methods=["patch"])
    # def change_manager(self, request):
    #     """Custom action to change farm manager"""
    #
    #     farm_id = request.data.get("id")
    #     manager_id = request.data.get("manager")
    #
    #     if not farm_id or not manager_id:
    #         return Response({"error": "Both farm and manager are required."},
    #                         status=status.HTTP_400_BAD_REQUEST)
    #
    #     try:
    #         farm = Farm.objects.get(Q(id=farm_id))
    #     except Farm.DoesNotExist:
    #         return Response({"error": "Farm not found."}, status=status.HTTP_404_NOT_FOUND)
    #
    #     try:
    #         manager = Employee.objects.get(Q(id=manager_id))
    #
    #     except Employee.DoesNotExist:
    #         return Response({"error": "Manager not found."}, status=status.HTTP_404_NOT_FOUND)
    #
    #     farm.manager = manager
    #     farm.save()
    #     message = f"{manager.user.get_full_name()} has been assigned as manager to '{farm.name}' farm."
    #
    #     return Response({"message": message}, status=status.HTTP_200_OK)


class FarmShedViewSet(viewsets.ModelViewSet):
    queryset = FarmShed.objects.all()
    serializer_class = FarmShedSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["name", "is_active", "capacity", "last_empty_date"]
    search_fields = ["name", "farm", "capacity", "last_empty_date", 'shed_metadata', 'is_active']
    ordering_fields = ["name", "farm", "capacity"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Shed created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Shed was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Shed was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)



class FarmShedViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'batch_id', 'shed', 'bird_type', 'initial_count', 'current_count',
        'expected_depletion_date', 'batch_details', 'status', 'created_by',
        'created_on', 'updated_by', 'updated_on'
    ]
    search_fields = [
        'batch_id', 'shed', 'bird_type', 'initial_count', 'current_count',
        'expected_depletion_date', 'batch_details', 'status', 'created_by',
        'created_on', 'updated_by', 'updated_on'
    ]
    ordering_fields = ["name", "current_count", "status"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Batch created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Batch was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Batch was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)



class DailyObservationViewSet(viewsets.ModelViewSet):
    queryset = DailyObservation.objects.all()
    serializer_class = DailyObservationSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'batch', 'mortality_count', 'culls', 'environmental_data', 'created_by',
        'created_on', 'updated_by', 'updated_on'
    ]
    search_fields = [
        'batch', 'mortality_count', 'culls', 'environmental_data', 'created_by',
        'created_on', 'updated_by', 'updated_on'
    ]
    ordering_fields = ["batch", "mortality_count", "created_on"]

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


class BreederFlockViewSet(viewsets.ModelViewSet):
    queryset = BreederFlock.objects.all()
    serializer_class = BreederFlockSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'source_batch', 'breed_line', 'genetic_source', 'traits', 'created_by',
        'created_on', 'updated_by', 'updated_on',
    ]
    search_fields = [
        'source_batch', 'breed_line', 'genetic_source', 'traits', 'created_by',
        'created_on', 'updated_by', 'updated_on',
    ]
    ordering_fields = ["source_batch", "breed_line", "genetic_source", "created_on"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Flock created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Flock was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Flock was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)



class IncubatorViewSet(viewsets.ModelViewSet):
    queryset = Incubator.objects.all()
    serializer_class = IncubatorSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'name', 'features', 'capacity', 'last_sanitized', 'is_active'
    ]
    search_fields = [
        'name', 'features', 'capacity', 'last_sanitized', 'is_active',
        'created_by', 'created_on', 'updated_by', 'updated_on'
    ]
    ordering_fields = ["name", "last_sanitized", "capacity", "created_on"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Incubator created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Incubator was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Incubator was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)


class IncubationCycleViewSet(viewsets.ModelViewSet):
    queryset = IncubationCycle.objects.all()
    serializer_class = IncubationCycleserializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'breeder_flock', 'expected_hatch_date', 'actual_hatch_date', 'hatcher', 'eggs_set_count'
    ]
    search_fields = [
        'cycle_id', 'breeder_flock', 'hatcher', 'eggs_set_count', 'status',
        'expected_hatch_date', 'incubation_logs', 'actual_hatch_date'
    ]
    ordering_fields = ["hatcher", "eggs_set_count", "status", "actual_hatch_date"]

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


class HatchRecordViewSet(viewsets.ModelViewSet):
    queryset = HatchRecord.objects.all()
    serializer_class = HatchRecordSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'incubation_cycle', 'is_added_to_inventory', 'destination_batch', 'cull_weight_total', 'total_chicks_hatched'
    ]
    search_fields = [
        'incubation_cycle', 'is_added_to_inventory', 'destination_batch',
        'total_chicks_hatched', 'grade_a_chicks', 'grade_b_chicks',
        'grade_c_chicks', 'quality_metrics', 'hatchability_percentage',
        'cull_weight_total'
    ]
    ordering_fields = ["grade_a_chicks", "grade_b_chicks", "grade_c_chicks", "cull_weight_total"]

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



class HealthProtocolViewSet(viewsets.ModelViewSet):
    queryset = HealthProtocol.objects.all()
    serializer_class = HealthProtocolSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'name', 'updated_by', 'created_by'
    ]
    search_fields = [
        'name', 'target_bird_type', 'protocol_steps','description',
        'created_by', 'created_on', 'updated_by', 'updated_on'
    ]
    ordering_fields = ["name", "created_on", "protocol_steps", "created_by"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Protocal created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Protocal was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Protocal was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = HealthProtocolSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'batch', 'date_of_administration', 'cost'
    ]
    search_fields = [
        'batch', 'date_of_administration', 'record_type', 'event_details', 'cost', 'notes',
        'withdrawal_end_date', 'created_by', 'created_on', 'updated_by',
        'updated_on'
    ]
    ordering_fields = ['batch', 'date_of_administration', 'record_type', 'event_details', 'cost']

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


class DiseaseOutbreakViewSet(viewsets.ModelViewSet):
    queryset = DiseaseOutbreak.objects.all()
    serializer_class = DiseaseOutbreakSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'batch', 'end_date', 'status'
    ]
    search_fields = [
        'batch', 'suspected_disease', 'end_date','diagnostic_data',
        'status', 'created_by', 'created_on', 'updated_by', 'updated_on'
    ]
    ordering_fields = ['batch', 'end_date', 'status']

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



class FarmVehicleViewSet(viewsets.ModelViewSet):
    queryset = FarmVehicle.objects.all()
    serializer_class = FarmVehicleSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'plate_number', 'vehicle_type', 'is_active'
    ]
    search_fields = [
        "plate_number", "vehicle_type", "max_payload_kg", "vehicle_specs"
        ,"is_active", "created_by", "created_on", "updated_by", "updated_on"
    ]
    ordering_fields = ['plate_number', 'vehicle_type', 'max_payload_kg']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        message = f"Vehicle created successfully"
        return Response({"message": message}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        message = f"Vehicle was updated successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        message = f"Vehicle was deleted successfully"
        return Response({"message" : message}, status=status.HTTP_200_OK)


class TransportMovementViewSet(viewsets.ModelViewSet):
    queryset = TransportMovement.objects.all()
    serializer_class =TransportMovementSerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'vehicle', 'driver', 'arrival_time'
    ]
    search_fields = [
        'vehicle', 'driver', 'origin', 'destination', 'departure_time',
        'arrival_time', 'transit_data', 'created_by', 'created_on',
        'updated_by', 'updated_on'
    ]
    ordering_fields = ['vehicle', 'origin', 'created_by']

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


class FarmManagerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ManagerHistory.objects.all()
    serializer_class = FarmManagerHistorySerializer
    pagination_class = GenericPaginator
    permission_classes = [CustomFarmPermissions]
    filter_backends = [ObjectPermissionsFilter]
