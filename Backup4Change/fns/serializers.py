from rest_framework import serializers
from django.utils import timezone
from .models import (
    FeedType, FeedInventory, FeedConsumption
)


now_iso = timezone.now().isoformat()

class FeedTypeSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()

    class Meta:
        model = FeedType
        fields = [
            'id', 'name', 'brand', 'composition', 'unit_price', 'created_by',
            'created_on', 'updated_by', 'updated_on'
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        return FeedType.objects.create(**validated_data)

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return FeedType.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None


class FeedInventorySerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    feed_type = serializers.SerializerMethodField()

    class Meta:
        model = FeedInventory
        fields = [
            'id', 'feed_type', 'total_quantity_kg', 'reorder_level',
            'stock_logs', 'created_by', 'created_on',
            'updated_by', 'updated_on'
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        return FeedInventory.objects.create(**validated_data)

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return FeedInventory.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_feed_type(self, obj) -> str:
        return obj.feed_type.name if obj.feed_type else None


class FeedConsumptionSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    feed_type = serializers.SerializerMethodField()
    batch = serializers.SerializerMethodField()

    class Meta:
        model = FeedConsumption
        fields = [
            'id', 'batch', 'feed_type', 'quantity_used_kg', 'consumption_notes',
            'waste_amount', 'created_by', 'created_on', 'updated_by', 'updated_on'
        ]

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        return FeedConsumption.objects.create(**validated_data)

    def update(self, instance, validated_data):
        request = self.context['request']
        validated_data['updated_by'] = request.user
        validated_data['updated_on'] = now_iso
        return FeedConsumption.objects.update(**validated_data)

    def get_created_by(self, obj) -> str:
        return obj.created_by.get_full_name() if obj.created_by else None

    def get_updated_by(self, obj) -> str:
        return obj.updated_by.get_full_name() if obj.updated_by else None

    def get_feed_type(self, obj) -> str:
        return obj.feed_type.name if obj.feed_type else None

    def get_batch(self, obj) -> str:
        return obj.batch.batch_id if obj.batch else 'Not specified'
