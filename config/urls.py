from django.contrib import admin
from django.urls import include, path
from dashboard.views import dashboard

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path("",dashboard,name="dashboard"),
    path("admin/", admin.site.urls),

    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),

    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),

    path(
        "api/",
        include("developers.urls"),
    ),

    path(
        "api/",
        include("locations.urls"),
    ),

    path(
        "api/",
        include("projects.urls"),
    ),

    path(
        "api/",
        include("inventory.urls"),
    ),
    path(
        "developers/",
        include("developers.urls"),
    ),
    path(
        "locations/",
        include("locations.urls"),
    ),
    path(
        "projects/",
        include("projects.urls"),
    ),
    path(
        "inventory/",
        include("inventory.urls"),
    ),
    path("", include("dashboard.urls")),
    path(
        "leads/",
        include("leads.urls")
    ),
    path("accounts/", include("accounts.urls")),
]