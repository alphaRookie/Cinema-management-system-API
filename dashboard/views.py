from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .services import DashboardService
from .permissions import IsManager


class DashboardAPIView(APIView):
    permission_classes = [IsManager, IsAuthenticated]

    def get(self, request):
        dashboard = DashboardService.get_full_manager_report()
        return Response(dashboard, status=status.HTTP_200_OK)
