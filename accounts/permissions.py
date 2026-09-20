from rest_framework.permissions import BasePermission


class CRMRolePermission(BasePermission):

    def has_permission(self, request, view):

        if not request.user.is_authenticated:
            return False

        role = request.user.role

        # Everyone authenticated can read
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return role in [
                "ADMIN",
                "MANAGER",
                "SALES",
                "VIEWER",
            ]

        # Viewer cannot create/update/delete
        if role == "VIEWER":
            return False

        # Sales cannot delete
        if role == "SALES" and request.method == "DELETE":
            return False

        # Admin, Manager and Sales can create/update
        if role in [
            "ADMIN",
            "MANAGER",
            "SALES",
        ]:
            return True

        # Only Admin and Manager can delete
        if role in [
            "ADMIN",
            "MANAGER",
        ] and request.method == "DELETE":
            return True

        return False