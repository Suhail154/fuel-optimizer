from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start_location = serializers.CharField(max_length=255)
    end_location = serializers.CharField(max_length=255)


class FuelStopSerializer(serializers.Serializer):
    stop_number = serializers.IntegerField()
    name = serializers.CharField()
    address = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    price_per_gallon = serializers.FloatField()
    gallons_to_purchase = serializers.FloatField()
    estimated_cost = serializers.FloatField()
    distance_from_start_miles = serializers.FloatField()
    distance_to_next_stop_miles = serializers.FloatField()
    detour_miles = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    start_location = serializers.CharField()
    end_location = serializers.CharField()
    total_distance_miles = serializers.FloatField()
    total_distance_km = serializers.FloatField()
    estimated_duration_hours = serializers.FloatField()
    starting_fuel_gallons = serializers.FloatField()
    starting_fuel_price_per_gallon = serializers.FloatField()
    starting_fuel_cost = serializers.FloatField()
    fuel_stops = FuelStopSerializer(many=True)
    total_fuel_needed_gallons = serializers.FloatField()
    total_estimated_fuel_cost = serializers.FloatField()
    average_price_per_gallon = serializers.FloatField()
    route_coordinates = serializers.ListField(
        child=serializers.ListField(child=serializers.FloatField())
    )
    summary = serializers.CharField()
