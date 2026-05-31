from common.mixins import BaseEnterpriseAuditSerializer
from wces.models import WasteCategory, WasteCollection


class WasteCategorySerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = WasteCategory
        fields = [
            "name",
            "disposal_method",
            "financial_logic",
            "requires_special_handling",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]


class WasteCollectionSerializers(BaseEnterpriseAuditSerializer):
    class Meta:
        model = WasteCollection
        fields = [
            "location",
            "category",
            "source_batch",
            "quantity_kg",
            "collection_details",
            "created_by",
            "updated_by",
            "created_on",
            "updated_on",
        ]
