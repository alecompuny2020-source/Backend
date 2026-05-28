from django.db import models
from common.mixins import BaseEnterpriseAuditModelMixin
from common.choices import ProductionStatus, UnitOfMeasure
from djmoney.models.fields import MoneyField
from django.utils.translation import gettext_lazy as _



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
        choices=ProductionStatus,
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
    input_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=10, choices=UnitOfMeasure.choices, default=UnitOfMeasure.KG)
    estimated_cost = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="TZS",
        verbose_name=_("Gharama kwa TZS"),
    )
    origin = models.ForeignKey('sfap.FarmBlock', on_delete=models.PROTECT, help_text="Meli/Kitalu gani imetoka")

    def __str__(self):
        return self.input_name


class FeedIngredientStock(BaseEnterpriseAuditModelMixin):
    """
    Inafuatilia stoki ya malighafi za chakula cha kuku zilizopo ghalani.
    """
    farm = models.ForeignKey(
        'sfap.Farm',
        on_delete=models.CASCADE,
        related_name="feed_stock",
        verbose_name=_("Farm Ingredient"),
    )
    ingredient_name = models.CharField(max_length=100) # Mfano: Alizeti, Mtama
    available_qty_kg = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    unit_cost_per_kg = MoneyField(
        max_digits=14,
        decimal_places=2,
        default_currency="TZS",
        verbose_name=_("Gharama kwa TZS"),
    )

    def __str__(self):
        return f"{self.ingredient_name} - {self.available_qty_kg} KG"
