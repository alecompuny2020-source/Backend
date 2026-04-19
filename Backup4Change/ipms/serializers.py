from rest_framework import serializers
from .models import Supplier
from helpers.choices import now, now_iso


class SupplierSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact', 'location', 'is_active', 'created_by',
            'updated_by', 'created_on', 'updated_on'
        ]
        extra_kwargs = {
            "read_only_fields" : {
                "id", "created_by", "created_on", "updated_by", "updated_on"
            }
        }

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        return Supplier.objects.create(**validated_data)

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validate_data['updated_on'] = now_iso
        return Supplier.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_is_active(self, obj) -> str:
        return 'YES' if obj.is_active else 'No'
