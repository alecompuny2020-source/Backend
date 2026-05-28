from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from sfap.models import CropProduction, FeedIngredientStock
from common.choices import current_time


class CropsManagementService:
    """
    Service layer ya kushughulikia uvunaji wa mazao na kuhamisha
    kama malighafi ya chakula cha mifugo.
    """

    @staticmethod
    @transaction.atomic
    def process_harvest_to_feed_stock(crop_production_id: int, actual_yield: Decimal, unit_cost_tzs: Decimal = Decimal('0.00')) -> FeedIngredientStock:
        """
        Inabadilisha hali ya mzunguko wa zao kuwa Imevunwa, inarekodi kiwango halisi,
        na kuongeza kiwango hicho moja kwa moja kwenye stoki ya chakula cha mifugo.
        """

        if actual_yield <= 0:
            raise ValidationError("Kiwango cha mavuno (actual_yield) lazima kiwe zaidi ya sifuri.")

        try:
            production = CropProduction.objects.select_for_update().get(id=crop_production_id)
        except CropProduction.DoesNotExist:
            raise ValidationError(f"Uzalishaji wa zao wenye ID {crop_production_id} haujapatikana.")

        if production.status == CropProduction.ProductionStatus.HARVESTED:
            raise ValidationError("Zao hili tayari lilikwisha wekwa kwenye hali ya 'Imevunwa'.")

        production.status = CropProduction.ProductionStatus.HARVESTED
        production.actual_yield_kg = actual_yield
        production.harvest_date = current_time.date()

        production.production_metadata['processed_to_feed_at'] = timezone.now().isoformat()
        production.production_metadata['financial_value_tzs'] = float(actual_yield * unit_cost_tzs)
        production.save()

        ingredient_stock, created = FeedIngredientStock.objects.select_for_update().get_or_create(
            ingredient_name__iexact=production.crop_name,
            defaults={
                'ingredient_name': production.crop_name.capitalize(),
                'available_qty_kg': Decimal('0.00'),
                'unit_cost_per_kg': unit_cost_tzs
            }
        )

        if not created and unit_cost_tzs > 0:
            total_existing_value = ingredient_stock.available_qty_kg * ingredient_stock.unit_cost_per_kg
            total_new_value = actual_yield * unit_cost_tzs
            total_qty = ingredient_stock.available_qty_kg + actual_yield

            if total_qty > 0:
                ingredient_stock.unit_cost_per_kg = (total_existing_value + total_new_value) / total_qty

        ingredient_stock.available_qty_kg += actual_yield
        ingredient_stock.save()

        return ingredient_stock
