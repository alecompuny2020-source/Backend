from django.db import models, transaction
from django.conf import settings
import uuid
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Avg
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from djmoney.models.fields import MoneyField
from helpers.choices import (
    BATCH_STATUS_CHOICES, BIRD_TYPE_CHOICES, CYCLE_STATUS,
    CURRENCY_CHOICES, HEALTH_RECORD_TYPE, OUTBREAK_STATUS
)
from utils.mixins import FarmAuditBaseModelMixin

# --- 1. MISINGI YA SHAMBA ---

class Farm(FarmAuditBaseModelMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, db_index=True)
    name = models.CharField(_("Farm Name"), max_length=255, unique=True)
    region = models.CharField(_("Region"), max_length=100)

    # Ikolojia Settings kwenye JSON
    site_config = models.JSONField(_("Site Configuration"), default=dict, blank=True)
    is_active = models.BooleanField(_("Is Active"), default=True)

    class Meta:
        db_table = "farm"

    def __str__(self):
        return f"{self.name} ({self.region})"

class FarmBlock(models.Model):
    """
    Vitalu vya Kilimo Ikolojia ndani ya Shamba.
    Hivi hutumika kwa mzunguko wa kuku (Rotational Grazing).
    """
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="blocks")
    name = models.CharField(max_length=100)
    size_acres = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=50, choices=[
        ('resting', 'Inapumzika'),
        ('grazing', 'Kuku wapo hapa'),
        ('cropping', 'Kuna Mazao')
    ], default='resting')

    # Data ya IoT
    soil_data = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.farm.name} - {self.name}"

# --- 2. USIMAMIZI WA KUKU (BATCH) ---

class Batch(FarmAuditBaseModelMixin):
    batch_id = models.CharField(_("Batch ID"), max_length=50, unique=True, db_index=True)
    farm = models.ForeignKey(Farm, on_delete=models.PROTECT, related_name="batches", null=True)
    current_block = models.ForeignKey(FarmBlock, on_delete=models.SET_NULL, null=True, blank=True)
    bird_type = models.CharField(_("Bird Type"), max_length=20, choices=BIRD_TYPE_CHOICES)
    initial_count = models.PositiveIntegerField(_("Initial Bird Count"))
    current_count = models.PositiveIntegerField(_("Current Bird Count"))

    status = models.CharField(_("Status"), max_length=20, choices=BATCH_STATUS_CHOICES, default="ACTIVE")
    batch_details = models.JSONField(_("Batch Details"), default=dict, blank=True)

    class Meta:
        db_table = "batch"

    def __str__(self):
        return self.batch_id

class DailyObservation(FarmAuditBaseModelMixin):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="observations")
    mortality_count = models.PositiveIntegerField(_("Mortality"), default=0)
    eggs_collected = models.IntegerField(_("Eggs Collected"), default=0)

    # Data ya mazingira (Temp, Humidity, nk)
    environmental_data = models.JSONField(_("Environmental Data"), default=dict)

    # Ikolojia: Mbolea iliyokusanywa
    manure_volume_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0.0)

    class Meta:
        db_table = "daily_observation"
        unique_together = ("batch", "created_on")

# --- 3. KILIMO IKOLOJIA NA MAZAO ---

class CropProduction(FarmAuditBaseModelMixin):
    """
    Inarekodi mazao yanayolimwa ili kulisha kuku au biashara,
    ikitumia mbolea kutoka kwa kuku.
    """
    block = models.ForeignKey(FarmBlock, on_delete=models.CASCADE)
    crop_name = models.CharField(max_length=100) # Mfano: Alizeti, Mtama
    planting_date = models.DateField()
    harvest_date = models.DateField(null=True, blank=True)

    # Mzunguko wa Virutubisho
    manure_used_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    production_metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.crop_name} - {self.block.name}"

class EcologicalInput(models.Model):
    """
    Inafuatilia pembejeo za asili (Organic Inputs)
    Kama vile: Wadudu (BSF), Nyasi, au Mbolea ya vimelea.
    """
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    input_name = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default="KG")
    origin = models.CharField(max_length=100, help_text="Meli/Kitalu gani imetoka")

    def __str__(self):
        return self.input_name

# --- 4. AFYA NA MAGONJYA (KUTOKA KWENYE FILE LAKO) ---

class MedicalRecord(FarmAuditBaseModelMixin):
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name="health_records")
    record_type = models.CharField(max_length=20, choices=HEALTH_RECORD_TYPE)
    event_details = models.JSONField(default=dict)
    cost = MoneyField(max_digits=14, decimal_places=2, default_currency="TZS")

    class Meta:
        db_table = "medical_record"
