"""
URL configuration for cinema project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [ # we only define prefix here, routes continues on urls in screening app
    path("admin/", admin.site.urls),
    path("screening", include("screening.urls")), # screening/...
    path("booking", include("booking.urls")),
    path("payment", include("payment.urls")),
    path("identity", include("identity.urls")),

    #Swagger/Redoc
    path('api/schema', SpectacularAPIView.as_view(), name='schema'), # This generates the "Schema" (the raw data)
    path('api/docs/swagger', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'), # This is the INTERACTIVE one (Swagger)
    path('api/docs/redoc', SpectacularRedocView.as_view(url_name='schema'), name='redoc'), # This is the BEAUTIFUL one (Redoc)
]
