from django.urls import path

from .views import (
    location_create,
    location_delete,
    location_detail,
    location_edit,
    location_list,
)


urlpatterns = [

    path(
        "",
        location_list,
        name="location_list",
    ),

    path(
        "add/",
        location_create,
        name="location_create",
    ),

    path(
        "<int:pk>/",
        location_detail,
        name="location_detail",
    ),

    path(
        "<int:pk>/edit/",
        location_edit,
        name="location_edit",
    ),

    path(
        "<int:pk>/delete/",
        location_delete,
        name="location_delete",
    ),
]