from django.urls import path

from .views import (
    project_create,
    project_delete,
    project_detail,
    project_edit,
    project_list,
    project_inventory,
    project_inventory_bhk,
)


urlpatterns = [

    path(
        "",
        project_list,
        name="project_list",
    ),

    path(
        "add/",
        project_create,
        name="project_create",
    ),

    path(
        "<int:pk>/",
        project_detail,
        name="project_detail",
    ),

    path(
        "<int:pk>/edit/",
        project_edit,
        name="project_edit",
    ),

    path(
        "<int:pk>/delete/",
        project_delete,
        name="project_delete",
    ),
    path(
        "<int:project_id>/inventory/",
        project_inventory,
        name="project_inventory",
    ),

    path(
        "<int:project_id>/inventory/<str:bhk>/",
        project_inventory_bhk,
        name="project_inventory_bhk",
    ),
]