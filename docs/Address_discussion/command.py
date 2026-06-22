osm2pgsql -d jina_la_database_yako -U postgres -H localhost tanzania-latest.osm.pbf

CREATE EXTENSION IF NOT EXISTS pg_trgm;


from rest_framework import viewsets, status
from rest_framework.response import Response
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q
from my_osm_app.models import PlanetOsmPoint  # Hili ni jedwali lililoingizwa kutoka OSM

class LocalAutocompleteViewSet(viewsets.ViewSet):
    """
    Injini ya Ndani ya Autocomplete (Self-Hosted Autocomplete Engine).
    Inatafuta maeneo ndani ya database yako ya PostgreSQL bila kutumia API ya nje.
    """

    def list(self, request):
        query = request.query_params.get('q', '').strip()

        if len(query) < 3:
            return Response([])  # Usitafute mpaka herufi zifike 3 ili kuzuia database overhead

        # 1. Tafuta maeneo yanayofanana kwa kutumia Trigram Similarity (Inavumilia makosa ya uandishi)
        # Tunatafuta kwenye maeneo yenye majina (amenity, shop, tourism, au highway)
        maeneo = PlanetOsmPoint.objects.annotate(
            similarity=TrigramSimilarity('name', query)
        ).filter(
            Q(similarity__gt=0.2) | Q(name__icontains=query)
        ).order_index("-similarity")[:10]  # Leta matokeo 10 bora tu

        results = []
        for eneo in maeneo:
            # Geuza PostGIS Point kwenda Lat/Lon
            # Kwenye PostGIS, eneo.way ni geometry object (ST_Transform inaweza kuhitajika kwenda 4326 ikiwa haipo)
            lon, lat = eneo.way.x, eneo.way.y

            # Jenga ule muundo kamili wa Bolt JSON ulioutamani!
            results.append({
                "id": f"LOC{eneo.osm_id}",
                "name": eneo.name,
                "shortName": f"<b>{query}</b>{eneo.name[len(query):]}" if eneo.name.lower().startswith(query.lower()) else eneo.name,
                "description": eneo.tags.get('description', ''),
                "address": {
                    "point": {
                        "region": {"id": None, "name": eneo.tags.get('addr:region', 'Dodoma Region'), "typeId": None, "type": None},
                        "subregion": {"id": None, "name": eneo.tags.get('addr:subregion', 'Dodoma Municipal'), "typeId": None, "type": None},
                        "place": {"id": None, "name": eneo.tags.get('addr:city', 'Dodoma'), "typeId": None, "type": "city"},
                        "addr": {"id": eneo.osm_id, "name": eneo.name, "typeId": None, "type": None},
                        "street": {"id": None, "name": eneo.tags.get('addr:street', ''), "typeId": None, "type": "Road"},
                        "zone": {"id": None, "name": eneo.tags.get('addr:suburb', ''), "typeId": None, "type": None},
                        "title": eneo.name,
                        "subtitle": eneo.tags.get('addr:full', ''),
                        "predefinedName": None,
                        "house": eneo.tags.get('addr:housenumber', None),
                        "lat": lat,
                        "lon": lon,
                        "entrance": None,
                        "type": None
                    },
                    "meta": {
                        "zoneFound": True,
                        "addressHistoryOccasionalId": 0,
                        "addressPatternId": None,
                        "meetPointsExists": False,
                        "patternName": None,
                        "category": "UrbanPoi" if eneo.amenity else "Street",
                        "isFinal": True,
                        "isFakeHouse": None
                    }
                },
                "addressType": eneo.amenity or eneo.shop or "location"
            })

        return Response(results, status=status.HTTP_200_OK)


from django.db import models, transaction
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point

# Hakikisha unavuta Mixin yako ya Enterprise kwa usahihi
# kutoka kwenye programu husika (mfano: kutoka apps.core.mixins)
# from apps.core.mixins import BaseEnterpriseModelMixin

class UserAddress(BaseEnterpriseModelMixin):
    """
    Enterprise Unified Address Model.
    Inaunganisha sifa zote za kibiashara za mfumo wako (AddressType, Audit Logging, Mixins)
    pamoja na muundo wa kijiografia uliogawanyika (Geographical Hierarchy) na mahesabu
    ya PostGIS ya akina Bolt/Maxim kwa ajili ya soko la Tanzania nzima.
    """

    # 1. Mahusiano na Ulinzi wa Kibiashara (Business Core Fields)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses"
    )
    address_type = models.ForeignKey(
        "core.AddressType",
        on_delete=models.CASCADE,
        related_name="user_addresses"
    )
    is_default = models.BooleanField(_("Default Address"), default=False)

    # API Automation Mapping (Kwa ajili ya utafutaji wa ndani au wa nje)
    external_id = models.CharField(
        _("External API ID"),
        max_length=100,
        unique=True,
        db_index=True,
        null=True,
        blank=True,
        help_text="Inahifadhi ID kutoka kwenye mfumo wa utafutaji/OSM"
    )
    name = models.CharField(
        _("Full Display Name"),
        max_length=255,
        help_text="Jina zima la anuani mfano: Hombolo Bus Stand"
    )
    category = models.CharField(_("Category"), max_length=50, default="UrbanPoi")  # mfano: Street, UrbanPoi
    api_address_type = models.CharField(_("API Address Type"), max_length=50, null=True, blank=True)  # mfano: bus_stop, restaurant

    # 2. Miundo ya Kijiografia Iliyonyooka (Normalized Geographical Hierarchy)
    country = models.CharField(_("Country"), max_length=100, default="Tanzania")
    region_name = models.CharField(_("Region/Mkoa"), max_length=100, default="Dodoma Region")
    subregion_name = models.CharField(_("Subregion/Municipal/Wilaya"), max_length=100, null=True, blank=True)
    place_name = models.CharField(_("Place/City/Mji"), max_length=100, default="Dodoma")
    street_name = models.CharField(_("Street/Road/Barabara"), max_length=100, null=True, blank=True)
    zone_name = models.CharField(_("Zone/Neighborhood/Kata"), max_length=100, null=True, blank=True)

    # 3. Injini ya Kijiografia (PostGIS Point Field)
    location_gps = gis_models.PointField(
        _("GPS Coordinates"),
        geography=True,
        srid=4326,
        db_index=True
    )

    # 4. Takwimu za Usafirishaji (Internal Logistics Metrics)
    distance_from_hub_km = models.DecimalField(
        _("Distance from Hub (KM)"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    estimated_delivery_fee = models.DecimalField(
        _("Estimated Delivery Fee"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_address"
        verbose_name = _("User Address")
        verbose_name_plural = _("User Addresses")
        # Inazuia mtumiaji kuwa na address zaidi ya moja ya aina ile ile (mfano: Hawezi kuwa na 'Home' mbili)
        unique_together = ("user", "address_type")

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.address_type.title()})"

    def get_log_message(self, old_data=None):
        """Usimamizi wa Audit Logging kutoka jedwali lako la kwanza"""
        if old_data:
            return f"Updated {self.address_type.title()} Address from: {old_data} to: {self.name}, {self.region_name}"
        return f"Added {self.address_type.title()} Address : {self.name}, {self.region_name}"

    def save(self, *args, **kwargs):
        """
        AUTOMATION PIPELINE:
        1. Inahakikisha kuna default address moja tu kwa mtumiaji.
        2. Inapiga mahesabu ya umbali na gharama kiotomatiki kupitia PostGIS.
        """
        # A. Udhibiti wa Default Address (Miamala salama ya Atomic)
        if self.is_default:
            with transaction.atomic():
                UserAddress.objects.filter(
                    user=self.user,
                    address_type=self.address_type
                ).exclude(pk=self.pk).update(is_default=False)

        # B. Injini ya Mahesabu ya Kijiografia (PostGIS Core)
        # Mfano: Point kuu ya biashara yako (Dodoma Central Hub: Longitude 35.7516, Latitude -6.1630)
        HUB_POINT = Point(35.7516, -6.1630, srid=4326)

        if self.location_gps:
            # Piga hesabu ya umbali mnyooka wa kijiografia (kwa mita, kisha geuza kwenda KM)
            distance_meters = HUB_POINT.distance(self.location_gps) * 100000
            self.distance_from_hub_km = round(distance_meters / 1000, 2)

            # Mfumo wa kikokotoo cha bei: Base Tsh 2,000 + (KM * Tsh 800)
            self.estimated_delivery_fee = 2000.00 + (float(self.distance_from_hub_km) * 800.00)

        super().save(*args, **kwargs)
