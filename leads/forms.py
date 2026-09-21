from django import forms

from .models import Lead, LeadActivity
from accounts.models import User


class LeadForm(forms.ModelForm):

    class Meta:
        model = Lead

        fields = [
            "name",
            "phone",
            "email",
            "source",
            "status",
            "interested_project",
            "budget_min",
            "budget_max",
            "preferred_location",
            "preferred_property_type",
            "bhk",
            "requirement",
            "next_follow_up",
            "assigned_to",
            "notes",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter lead name"
                }
            ),

            "phone": forms.TextInput(
                attrs={
                    "placeholder": "Enter phone number"
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter email"
                }
            ),

            "budget_min": forms.NumberInput(
                attrs={
                    "placeholder": "Minimum budget"
                }
            ),

            "budget_max": forms.NumberInput(
                attrs={
                    "placeholder": "Maximum budget"
                }
            ),

            "preferred_location": forms.TextInput(
                attrs={
                    "placeholder": "Example: Kokapet, Kollur, Mokila"
                }
            ),

            "preferred_property_type": forms.TextInput(
                attrs={
                    "placeholder": "Villa / Apartment / Plot"
                }
            ),

            "bhk": forms.NumberInput(
                attrs={
                    "min": 1,
                    "max": 10
                }
            ),

            "requirement": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Customer requirement"
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Additional notes"
                }
            ),

            "next_follow_up": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local"
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):

        super().__init__(*args, **kwargs)

        # -----------------------------------------
        # Only active Sales users
        # -----------------------------------------

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

        # -----------------------------------------
        # Sales users cannot choose assignment
        # -----------------------------------------

        if user and user.role == User.Role.SALES:
                # Show the logged-in sales user
                self.fields["assigned_to"].initial = user

                # Sales cannot change assignment
                self.fields["assigned_to"].disabled = True


class LeadActivityForm(forms.ModelForm):

    class Meta:
        model = LeadActivity

        fields = [
            "activity_type",
            "subject",
            "description",
            "activity_date",
        ]

        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "placeholder": "Example: Follow-up call"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Enter activity details"
                }
            ),

            "activity_date": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local"
                }
            ),
        }