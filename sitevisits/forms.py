from django import forms

from .models import SiteVisit
from accounts.models import User


class SiteVisitForm(forms.ModelForm):

    class Meta:
        model = SiteVisit

        fields = [
            "lead",
            "project",
            "assigned_to",
            "visit_date",
            "visit_time",
            "status",
            "notes",
            "outcome",
        ]

        widgets = {
            "lead": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "project": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "assigned_to": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "visit_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),

            "visit_time": forms.TimeInput(
                attrs={
                    "class": "form-control",
                    "type": "time",
                }
            ),

            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter visit notes...",
                }
            ),

            "outcome": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Enter visit outcome...",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):

        super().__init__(*args, **kwargs)

        # Only active Sales users
        self.fields["assigned_to"].queryset = User.objects.filter(
            role=User.Role.SALES,
            is_active=True,
        ).order_by(
            "first_name",
            "last_name",
            "username",
        )

        self.fields["assigned_to"].required = False
        self.fields["assigned_to"].empty_label = "Unassigned"

        # ------------------------------------------------
        # SALES USER
        # ------------------------------------------------

        if user and user.role == User.Role.SALES:

            # New site visit
            if not self.instance.pk:
                self.fields["assigned_to"].initial = user

            # Existing site visit
            elif self.instance.assigned_to:
                self.fields["assigned_to"].initial = (
                    self.instance.assigned_to
                )

            # Sales cannot change assignment
            self.fields["assigned_to"].disabled = True

            # Sales should only select their own leads
            self.fields["lead"].queryset = (
                self.fields["lead"].queryset.filter(
                    assigned_to=user
                )
            )