from django.urls import path
from . import views

urlpatterns = [
    path("", views.lead_list, name="lead_list"),
    path("add/", views.lead_create, name="lead_create"),
    path("<int:pk>/", views.lead_detail, name="lead_detail"),
    path("<int:pk>/edit/", views.lead_edit, name="lead_edit"),
    path("<int:pk>/delete/", views.lead_delete, name="lead_delete"),
    path("<int:pk>/activity/add/",views.lead_activity_create,name="lead_activity_create"),
    path(
        "<int:pk>/activity/<int:activity_id>/edit/",
        views.lead_activity_edit,
        name="lead_activity_edit",
    ),

    path(
        "<int:pk>/activity/<int:activity_id>/delete/",
        views.lead_activity_delete,
        name="lead_activity_delete",
    ),
    path(
        "<int:pk>/status/",
        views.lead_status_update,
        name="lead_status_update",
    ),
    path(
        "pipeline/",
        views.lead_pipeline,
        name="lead_pipeline",
    ),
]