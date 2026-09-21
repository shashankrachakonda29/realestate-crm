from django.urls import path

from . import views


urlpatterns = [

    path(
        "",
        views.sitevisit_list,
        name="sitevisit_list",
    ),

    path(
        "add/",
        views.sitevisit_create,
        name="sitevisit_create",
    ),

    path(
        "<int:pk>/",
        views.sitevisit_detail,
        name="sitevisit_detail",
    ),

    path(
        "<int:pk>/edit/",
        views.sitevisit_edit,
        name="sitevisit_edit",
    ),

    path(
        "<int:pk>/status/",
        views.sitevisit_status_update,
        name="sitevisit_status_update",
    ),

    path(
        "<int:pk>/delete/",
        views.sitevisit_delete,
        name="sitevisit_delete",
    ),
]