import logging

from django.db import transaction
from django.db.models.signals import post_migrate
from django.dispatch import receiver

from common.seeds.config_data import BREED_SEED_DATA, LOOKUP_SEED_DATA

logger = logging.getLogger(__name__)


@receiver(post_migrate)
def bootstrap_enterprise_lookups_and_taxonomy(sender, **kwargs):
    """
    Infrastructure Data Provisioner Engine.
    Executes sequentially on container deployment. Converts hardcoded configuration data
    into secure, indexable database rows across all lookups.
    """
    app_config = sender

    if app_config.label != "core":
        return

    logger.info("Initializing Enterprise Workflow Lookup Matrix Provisioning...")
    print("Initializing Enterprise Workflow Lookup Matrix Provisioning...")

    try:
        with transaction.atomic():

            for model_name, record_payloads in LOOKUP_SEED_DATA.items():
                try:
                    model_class = app_config.get_model(model_name)
                except LookupError:
                    logger.warning(
                        f"Model '{model_name}' haikupatikana kwenye app ya core. Tunairuka."
                    )
                    print(
                        f"Model '{model_name}' haikupatikana kwenye app ya core. Tunairuka."
                    )
                    continue

                for record in record_payloads:
                    model_class.objects.get_or_create(
                        code=record["code"],
                        defaults={
                            "name": record["name"],
                            "color_hex": record.get("color_hex", "#7F8C8D"),
                            "sort_order": record["sort_order"],
                            "is_active": True,
                        },
                    )

            try:
                SpeciesType = app_config.get_model("SpeciesType")
                BreedType = app_config.get_model("BreedType")

                for index, breed in enumerate(BREED_SEED_DATA, start=1):
                    species_obj = SpeciesType.objects.filter(
                        code=breed["species_code"]
                    ).first()
                    if not species_obj:
                        logger.warning(
                            f"Species yenye code '{breed['species_code']}' haikupatikana kwa ajili ya breed '{breed['name']}'."
                        )
                        print(
                            f"Species yenye code '{breed['species_code']}' haikupatikana kwa ajili ya breed '{breed['name']}'."
                        )
                        continue

                    BreedType.objects.get_or_create(
                        code=breed["code"],
                        defaults={
                            "name": breed["name"],
                            "species": species_obj,
                            "sort_order": index,
                            "is_active": True,
                        },
                    )
            except LookupError:
                logger.error("Kushindwa kupakia models za SpeciesType au BreedType.")
                print("Kushindwa kupakia models za SpeciesType au BreedType.")

        logger.info("All Enterprise Workflow Lookups successfully synced.")
        print("All Enterprise Workflow Lookups successfully synced.")

    except Exception as e:
        logger.error(f"Hitilafu ilitokea wakati wa ku-seed config data: {e}")
        print(f"Hitilafu ilitokea wakati wa ku-seed config data: {e}")
