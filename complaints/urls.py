from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ComplaintViewSet,
    public_complaints,
    public_stats,
)

router = DefaultRouter()
router.register("complaints", ComplaintViewSet, basename="complaint")

urlpatterns = [
    path("", include(router.urls)),
    path("public/complaints/", public_complaints),
    path("public/stats/", public_stats),
]