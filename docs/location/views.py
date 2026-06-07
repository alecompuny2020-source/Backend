# apps/sales/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.logistics.services import get_distance_and_time
from apps.sales.pricing import BoltPricingEngine

class EstimateTripFareView(APIView):
    """
    Endpoint ya kukadiria umbali, muda na nauli ya safari (Tsh)
    """
    def post(self, request, *args, **kwargs):
        # Kupokea maeneo kutoka kwenye App ya simu
        pickup_lat = request.data.get('pickup_lat')
        pickup_lng = request.data.get('pickup_lng')
        dropoff_lat = request.data.get('dropoff_lat')
        dropoff_lng = request.data.get('dropoff_lng')

        if not all([pickup_lat, pickup_lng, dropoff_lat, dropoff_lng]):
            return Response(
                {"error": "Tafadhali weka pickup na dropoff coordinates zote."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1. Piga hesabu ya umbali na muda barabarani
        distance_m, duration_s = get_distance_and_time(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)

        if distance_m is None:
            return Response(
                {"error": "Imeshindikana kupata njia ya barabara husika."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 2. Piga hesabu ya gharama za kitanzania (Tsh)
        estimated_fare = BoltPricingEngine.calculate_estimated_fare(distance_m, duration_s)

        # 3. Rudisha majibu safi kwenda kwenye App (Frontend)
        return Response({
            "distance_km": round(distance_m / 1000.0, 2),
            "duration_minutes": round(duration_s / 60.0, 1),
            "estimated_fare_tsh": estimated_fare,
            "currency": "TZS"
        }, status=status.HTTP_200_OK)
