from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import SetPasswordForm
from django.shortcuts import get_object_or_404, render, redirect

from .decorators import role_required
from .forms import UserCreateForm, UserUpdateForm


User = get_user_model()


# =====================================================
# LOGIN
# =====================================================

def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:

            if user.is_active:
                login(request, user)
                return redirect("dashboard")

        return render(
            request,
            "accounts/login.html",
            {
                "error": "Invalid username or password."
            }
        )

    return render(
        request,
        "accounts/login.html"
    )


# =====================================================
# LOGOUT
# =====================================================

def logout_view(request):

    logout(request)

    return redirect("login")


# =====================================================
# USER LIST
# =====================================================

@role_required("ADMIN")
def user_list(request):

    users = User.objects.all().order_by(
        "-is_active",
        "username",
    )

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": users,
        }
    )


# =====================================================
# CREATE USER
# =====================================================

@role_required("ADMIN")
def user_create(request):

    if request.method == "POST":

        form = UserCreateForm(
            request.POST
        )

        if form.is_valid():

            form.save()

            return redirect(
                "user_list"
            )

    else:

        form = UserCreateForm()

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": "Add User",
        }
    )


# =====================================================
# EDIT USER
# =====================================================

@role_required("ADMIN")
def user_edit(request, pk):

    user = get_object_or_404(
        User,
        pk=pk
    )

    if request.method == "POST":

        form = UserUpdateForm(
            request.POST,
            instance=user,
        )

        if form.is_valid():

            form.save()

            return redirect(
                "user_list"
            )

    else:

        form = UserUpdateForm(
            instance=user
        )

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": "Edit User",
            "user_obj": user,
        }
    )


# =====================================================
# CHANGE PASSWORD
# =====================================================

@role_required("ADMIN")
def user_password(request, pk):

    user = get_object_or_404(
        User,
        pk=pk
    )

    if request.method == "POST":

        form = SetPasswordForm(
            user,
            request.POST,
        )

        if form.is_valid():

            form.save()

            return redirect(
                "user_list"
            )

    else:

        form = SetPasswordForm(
            user
        )

    return render(
        request,
        "accounts/password_form.html",
        {
            "form": form,
            "user_obj": user,
        }
    )


# =====================================================
# ACTIVATE / DEACTIVATE
# =====================================================

@role_required("ADMIN")
def user_toggle_active(request, pk):

    user = get_object_or_404(
        User,
        pk=pk
    )

    if request.method == "POST":

        # Don't allow an admin to deactivate themselves
        if user.pk != request.user.pk:

            user.is_active = not user.is_active

            user.save(
                update_fields=["is_active"]
            )

    return redirect(
        "user_list"
    )


# =====================================================
# DELETE USER
# =====================================================

@role_required("ADMIN")
def user_delete(request, pk):

    user = get_object_or_404(
        User,
        pk=pk
    )

    # Prevent deleting yourself
    if user.pk == request.user.pk:
        return redirect(
            "user_list"
        )

    if request.method == "POST":

        user.delete()

        return redirect(
            "user_list"
        )

    return render(
        request,
        "accounts/user_delete.html",
        {
            "user_obj": user,
        }
    )