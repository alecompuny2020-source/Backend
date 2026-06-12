# apps/logistics/models.py
from django.contrib.gis.db import models  # Tumia models za GeoDjango


class DriverLocation(models.Model):
    driver = models.OneToOneField("employees.Employee", on_delete=models.CASCADE)
    # Point inahifadhi latitude na longitude kwa usahihi wa kijiografia
    coordinates = models.PointField(srid=4326)
    updated_at = models.DateTimeField(auto_now=True)
