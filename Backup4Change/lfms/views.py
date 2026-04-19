from django.shortcuts import render

# Create your views here.


# views.py
def request_ride(request):
    lat = request.data.get("lat")
    lng = request.data.get("lng")
    v_type = request.data.get("vehicle_type")  # e.g., 'CAR'

    # Get the top 5 closest drivers
    nearby_drivers = DispatcherService.get_closest_drivers(lat, lng, v_type)

    if not nearby_drivers:
        return Response({"error": "No available drivers nearby"}, status=404)

    return Response(nearby_drivers)
