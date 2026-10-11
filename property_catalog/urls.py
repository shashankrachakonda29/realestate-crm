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
        "preview/",
        views.preview,
        name="preview",
    ),
   

]