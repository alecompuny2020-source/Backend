# apps/logistics/services.py
import requests
from django.conf import settings


def get_distance_and_time(origin_lat, origin_lng, dest_lat, dest_lng):
    """
    Inavuta umbali (mita) na muda (sekunde) halisi wa barabarani kutoka Google Maps
    """
    api_key = settings.GOOGLE_MAPS_API_KEY
    url = (
        f"https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={origin_lat},{origin_lng}"
        f"&destinations={dest_lat},{dest_lng}"
        f"&mode=driving"
        f"&key={api_key}"
    )

    response = requests.get(url).json()

    if response["status"] == "OK":
        element = response["rows"][0]["elements"][0]
        if element["status"] == "OK":
            distance_meters = element["distance"][
                "value"
            ]  # Mfano: 5000 (mita 5000 = km 5)
            duration_seconds = element["duration"][
                "value"
            ]  # Mfano: 1200 (sekunde 1200 = dk 20)
            return distance_meters, duration_seconds

    return None, None
