from datetime import datetime, timezone

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .fuel_data import load_fuel_stops
from .fuel_optimizer import FuelOptimizer
from .routing_service import RoutingService
from .serializers import RouteRequestSerializer, RouteResponseSerializer


class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })


class RouteOptimizationView(APIView):
    def post(self, request):
        serializer = RouteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        start = serializer.validated_data['start_location']
        end = serializer.validated_data['end_location']

        route = RoutingService().get_route(start, end)
        if not route['success']:
            return Response({'error': route['error']}, status=status.HTTP_400_BAD_REQUEST)

        result = FuelOptimizer(load_fuel_stops()).optimize_route(route, start, end)
        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RouteResponseSerializer(result['route_data']).data)


class FuelStopsView(APIView):
    def get(self, request):
        state = request.query_params.get('state', '').strip().upper()
        if not state:
            return Response(
                {'error': 'state parameter is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            limit = min(int(request.query_params.get('limit', 20)), 100)
        except ValueError:
            limit = 20

        stops = load_fuel_stops()
        in_state = stops[stops['State'].str.upper() == state]
        if in_state.empty:
            return Response(
                {'error': f'No fuel stops found for state {state}'},
                status=status.HTTP_404_NOT_FOUND,
            )

        cheapest = in_state.nsmallest(limit, 'Retail Price')
        return Response({
            'state': state,
            'total_stops': len(in_state),
            'displayed_stops': len(cheapest),
            'stops': [
                {
                    'id': int(row['OPIS Truckstop ID']),
                    'name': row['Truckstop Name'],
                    'city': row['City'],
                    'address': row['Address'],
                    'price_per_gallon': float(row['Retail Price']),
                }
                for _, row in cheapest.iterrows()
            ],
        })
