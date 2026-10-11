from django.urls import path,include

from . import views


app_name = "property_catalog"


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),

    path(
        "import/",
        views.import_json,
        name="import_json",
    ),

    path(
        "<int:pk>/",
        views.catalog_detail,
        name="catalog_detail",
    ),
    path(
        "<int:catalog_pk>/developers/add/",
        views.catalog_developer_create,
        name="catalog_developer_create",
    ),
    path(
        "<int:catalog_pk>/developers/<int:developer_pk>/",
        views.catalog_developer_detail,
        name="catalog_developer_detail",
    ),
    path(
        "<int:catalog_pk>/developers/<int:developer_pk>/projects/add/",
        views.catalog_project_create,
        name="catalog_project_create",
    ),
    path(
        "<int:catalog_pk>/projects/<int:project_pk>/",
        views.catalog_project_detail,
        name="catalog_project_detail",
    ),
    path(
        "<int:catalog_pk>/projects/<int:project_pk>/configurations/add/",
        views.catalog_configuration_create,
        name="catalog_configuration_create",
    ),
    path(
        "preview/",
        views.preview,
        name="preview",
    ),
   

]