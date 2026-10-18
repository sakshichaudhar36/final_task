from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    ComplaintViewSet,
    public_complaints,
    public_stats,
    management_analytics,
)
router = DefaultRouter()
router.register(
    "complaints",
    ComplaintViewSet,
    basename="complaint",
)
urlpatterns = [
    path("", include(router.urls)),
    path("public/complaints/", public_complaints, name="public-complaints"),
    path("public/stats/", public_stats, name="public-stats"),
    path(
        "management/analytics/",
        management_analytics,
        name="management-analytics",
    ),
]