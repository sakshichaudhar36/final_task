from django.urls import path
from .views import CampusLocationListView

urlpatterns = [
    path("locations/", CampusLocationListView.as_view(), name="locations"),
]