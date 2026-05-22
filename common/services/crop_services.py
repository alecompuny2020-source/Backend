from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import CropProduction
# Badilisha hapa kuendana na eneo halisi la modeli yako ya chakula cha kuku
from sfap.models import FeedIngredientStock

class CropHarvestLogisticsService:
    """
    Service layer ya kushughulikia uvunaji wa mazao na kuhamisha
    kama malighafi ya chakula cha kuku (Poultry Feed Raw Materials).
    """

    @staticmethod
    @transaction.atomic
    def process_harvest_to_feed_stock(crop_production_id: int, actual_yield: Decimal, unit_cost_tzs: Decimal = Decimal('0.00')) -> FeedIngredientStock:
        """
        Inabadilisha hali ya mzunguko wa zao kuwa Imevunwa, inarekodi kiwango halisi,
        na kuongeza kiwango hicho moja kwa moja kwenye stoki ya chakula cha kuku.
        """
        if actual_yield <= 0:
            raise ValidationError("Kiwango cha mavuno (actual_yield) lazima kiwe zaidi ya sifuri.")

        # 1. Pata na ufunge data ya uzalishaji kwa usalama (Pessimistic locking kuzuia race conditions)
        try:
            production = CropProduction.objects.select_for_update().get(id=crop_production_id)
        except CropProduction.DoesNotExist:
            raise ValidationError(f"Uzalishaji wa zao wenye ID {crop_production_id} haujapatikana.")

        # Kuzuia kurudia kuvuna zao lililovunwa tayari
        if production.status == CropProduction.ProductionStatus.HARVESTED:
            raise ValidationError("Zao hili tayari lilikwisha wekwa kwenye hali ya 'Imevunwa'.")

        # 2. Update CropProduction metadata na status
        production.status = CropProduction.ProductionStatus.HARVESTED
        production.actual_yield_kg = actual_yield
        production.harvest_date = timezone.now().date()

        # Kuhifadhi kumbukumbu ya ziada kwenye JSON metadata field
        production.production_metadata['processed_to_feed_at'] = timezone.now().isoformat()
        production.production_metadata['financial_value_tzs'] = float(actual_yield * unit_cost_tzs)
        production.save()

        # 3. Update au Create stoki ya chakula cha kuku (Feed Ingredient Stock)
        # Tunatumia ie. jina la zao kama kitambulisho cha kiungo cha chakula
        ingredient_stock, created = FeedIngredientStock.objects.select_for_update().get_or_create(
            ingredient_name__iexact=production.crop_name,
            defaults={
                'ingredient_name': production.crop_name.capitalize(),
                'available_qty_kg': Decimal('0.00'),
                'unit_cost_per_kg': unit_cost_tzs
            }
        )

        # Kama stoki ilikuwepo, tunapiga mahesabu mapya ya Wastani wa Bei (Moving Average Cost) kama ikibidi
        if not created and unit_cost_tzs > 0:
            total_existing_value = ingredient_stock.available_qty_kg * ingredient_stock.unit_cost_per_kg
            total_new_value = actual_yield * unit_cost_tzs
            total_qty = ingredient_stock.available_qty_kg + actual_yield

            if total_qty > 0:
                ingredient_stock.unit_cost_per_kg = (total_existing_value + total_new_value) / total_qty

        # Ongeza mzigo ghalani
        ingredient_stock.available_qty_kg += actual_yield
        ingredient_stock.save()

        return ingredient_stock
