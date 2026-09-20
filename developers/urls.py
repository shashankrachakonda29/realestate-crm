from django.urls import path

from .views import (
    developer_create,
    developer_delete,
    developer_detail,
    developer_edit,
    developer_list,
)


urlpatterns = [
    path(
        "",
        developer_list,
        name="developer_list",
    ),

    path(
        "add/",
        developer_create,
        name="developer_create",
    ),

    path(
        "<int:pk>/",
        developer_detail,
        name="developer_detail",
    ),

    path(
        "<int:pk>/edit/",
        developer_edit,
        name="developer_edit",
    ),

    path(
        "<int:pk>/delete/",
        developer_delete,
        name="developer_delete",
    ),
]