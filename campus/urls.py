from rest_framework.routers import DefaultRouter
from .views import CampusLocationViewSet
router = DefaultRouter()
router.register(
    "locations",
    CampusLocationViewSet,
    basename="location",
)
urlpatterns = router.urls