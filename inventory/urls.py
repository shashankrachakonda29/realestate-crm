from django.urls import path

from .views import (
    inventory_create,
    inventory_delete,
    inventory_detail,
    inventory_edit,
    inventory_list,
    inventory_import,
)


urlpatterns = [

    path(
        "",
        inventory_list,
        name="inventory_list",
    ),

    path(
        "add/",
        inventory_create,
        name="inventory_create",
    ),

    path(
        "import/",
        inventory_import,
        name="inventory_import",
    ),

    path(
        "<int:pk>/",
        inventory_detail,
        name="inventory_detail",
    ),

    path(
        "<int:pk>/edit/",
        inventory_edit,
        name="inventory_edit",
    ),

    path(
        "<int:pk>/delete/",
        inventory_delete,
        name="inventory_delete",
    ),
]