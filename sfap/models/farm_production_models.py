from django.db import models
from common.mixins import BaseEnterpriseAuditModelMixin


class CropProduction(BaseEnterpriseAuditModelMixin):
    """
    Inarekodi mazao yanayolimwa ili kulisha kuku au biashara,
    ikitumia mbolea kutoka kwa kuku.
    """
    block = models.ForeignKey('sfap.FarmBlock', on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100) # Mfano: Alizeti, Mtama
    planting_date = models.DateField()
    harvest_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=ProductionStatus.choices,
        default=ProductionStatus.PLANTED
    )

    # Mzunguko wa Virutubisho
    manure_used_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    production_metadata = models.JSONField(default=dict, blank=True)
    estimated_yield_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    actual_yield_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.crop_name} - {self.block.name}"



class EcologicalInput(BaseEnterpriseAuditModelMixin):
    """
    Inafuatilia pembejeo za asili (Organic Inputs)
    Kama vile: Wadudu (BSF), Nyasi, au Mbolea ya vimelea.
    """
    farm = models.ForeignKey('sfap.Farm', on_delete=models.CASCADE)
    input_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default="KG")
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, help_text="Gharama kwa TZS")
    origin = models.ForeignKey('sfap.FarmBlock', on_delete=models.PROTECT, help_text="Meli/Kitalu gani imetoka")

    def __str__(self):
        return self.input_name
