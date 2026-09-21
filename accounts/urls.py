from django.urls import path

from . import views


urlpatterns = [

    # Authentication
    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    # User Management
    path(
        "users/",
        views.user_list,
        name="user_list",
    ),

    path(
        "users/create/",
        views.user_create,
        name="user_create",
    ),

    path(
        "users/<int:pk>/edit/",
        views.user_edit,
        name="user_edit",
    ),

    path(
        "users/<int:pk>/password/",
        views.user_password,
        name="user_password",
    ),

    path(
        "users/<int:pk>/toggle-active/",
        views.user_toggle_active,
        name="user_toggle_active",
    ),

    path(
        "users/<int:pk>/delete/",
        views.user_delete,
        name="user_delete",
    ),

]