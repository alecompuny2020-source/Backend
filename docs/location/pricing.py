# apps/sales/pricing.py

class BoltPricingEngine:
    BASE_FARE = 1500.00      # Gharama ya kuanzia (Tsh)
    PER_KM_RATE = 800.00     # Gharama kwa kila Kilomita moja (Tsh)
    PER_MINUTE_RATE = 150.00 # Gharama kwa kila dakika moja safarini (Tsh)

    @classmethod
    def calculate_estimated_fare(cls, distance_meters, duration_seconds):
        distance_km = distance_meters / 1000.0
        duration_minutes = duration_seconds / 60.0

        # Hesabu ya nauli ya msingi
        distance_cost = distance_km * cls.PER_KM_RATE
        time_cost = duration_minutes * cls.PER_MINUTE_RATE

        total_fare = cls.BASE_FARE + distance_cost + time_cost

        # Kurudisha nauli iliyofungwa kwenye mamia ya karibu (Mfano: 4,520 inakuwa 4,500)
        return round(total_fare, -2)
