import json
import re

from django import forms

from .models import (
    CatalogConfiguration,
    CatalogDeveloper,
    CatalogProject,
    PropertyCatalog,
)
from .services import PropertyCatalogImportError, validate_catalog_data


class PropertyCatalogImportForm(forms.Form):

    target_catalog = forms.ModelChoiceField(
        queryset=PropertyCatalog.objects.none(),
        required=False,
        label="Add to an existing catalog",
        empty_label="Create a new catalog",
    )

    json_file = forms.FileField(
        label="Property JSON File",
        help_text=(
            "Upload a JSON file containing developers, "
            "projects, locations and configurations."
        ),
        widget=forms.ClearableFileInput(
            attrs={
                "accept": ".json,application/json",
            }
        ),
    )

    def clean_json_file(self):

        file = self.cleaned_data["json_file"]


        # ==============================
        # FILE EXTENSION
        # ==============================

        if not file.name.lower().endswith(".json"):

            raise forms.ValidationError(
                "Only JSON files are allowed."
            )


        # ==============================
        # FILE SIZE
        # ==============================

        if file.size == 0:

            raise forms.ValidationError(
                "The uploaded file is empty."
            )


        # ==============================
        # READ JSON
        # ==============================

        try:

            file.seek(0)

            raw_data = file.read()

            data = json.loads(
                raw_data.decode("utf-8")
            )

        except UnicodeDecodeError:

            raise forms.ValidationError(
                "The JSON file must use UTF-8 encoding."
            )

        except json.JSONDecodeError as exc:

            raise forms.ValidationError(
                f"Invalid JSON format: {exc}"
            )


        # ==============================
        # ROOT VALIDATION
        # ==============================

        if not isinstance(data, dict):

            raise forms.ValidationError(
                "JSON root must be an object."
            )


        # ==============================
        # DEVELOPERS
        # ==============================

        developers = data.get(
            "developers"
        )

        if developers is None:

            raise forms.ValidationError(
                "JSON must contain a 'developers' field."
            )


        if not isinstance(
            developers,
            list,
        ):

            raise forms.ValidationError(
                "'developers' must be a list."
            )


        if not developers:

            raise forms.ValidationError(
                "At least one developer is required."
            )


        # ==============================
        # DEVELOPER VALIDATION
        # ==============================

        for developer_index, developer in enumerate(
            developers,
            start=1,
        ):

            if not isinstance(
                developer,
                dict,
            ):

                raise forms.ValidationError(
                    f"Developer {developer_index} must be an object."
                )


            if not developer.get("name"):

                raise forms.ValidationError(
                    f"Developer {developer_index} must have a name."
                )


            projects = developer.get(
                "projects",
                [],
            )


            if not isinstance(
                projects,
                list,
            ):

                raise forms.ValidationError(
                    f"Projects for developer "
                    f"'{developer.get('name')}' must be a list."
                )


            # ==============================
            # PROJECT VALIDATION
            # ==============================

            for project_index, project in enumerate(
                projects,
                start=1,
            ):

                if not isinstance(
                    project,
                    dict,
                ):

                    raise forms.ValidationError(
                        f"Project {project_index} "
                        f"under '{developer.get('name')}' "
                        f"must be an object."
                    )


                if not project.get("name"):

                    raise forms.ValidationError(
                        f"Project {project_index} "
                        f"under '{developer.get('name')}' "
                        f"must have a name."
                    )


                configurations = project.get(
                    "configurations",
                    [],
                )


                if not isinstance(
                    configurations,
                    list,
                ):

                    raise forms.ValidationError(
                        f"Configurations for project "
                        f"'{project.get('name')}' "
                        f"must be a list."
                    )


                # ==============================
                # CONFIGURATION VALIDATION
                # ==============================

                for configuration_index, configuration in enumerate(
                    configurations,
                    start=1,
                ):

                    if not isinstance(
                        configuration,
                        dict,
                    ):

                        raise forms.ValidationError(
                            f"Configuration "
                            f"{configuration_index} "
                            f"under project "
                            f"'{project.get('name')}' "
                            f"must be an object."
                        )


                    if not configuration.get(
                        "property_type"
                    ):

                        raise forms.ValidationError(
                            f"Configuration "
                            f"{configuration_index} "
                            f"under project "
                            f"'{project.get('name')}' "
                            f"must have 'property_type'."
                        )


                    if not configuration.get(
                        "type_name"
                    ):

                        raise forms.ValidationError(
                            f"Configuration "
                            f"{configuration_index} "
                            f"under project "
                            f"'{project.get('name')}' "
                            f"must have 'type_name'."
                        )

        try:
            validate_catalog_data(data)
        except PropertyCatalogImportError as exc:
            raise forms.ValidationError(str(exc)) from exc

        # ==============================
        # STORE PARSED DATA
        # ==============================

        self.cleaned_data[
            "catalog_data"
        ] = data


        # Reset file pointer
        file.seek(0)


        return file

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_catalog"].queryset = PropertyCatalog.objects.order_by(
            "-created_at"
        )




    def parse_json(self, uploaded_file):
        """Return validated JSON data from the uploaded file."""

        if "catalog_data" in self.cleaned_data:
            return self.cleaned_data["catalog_data"]

        if uploaded_file is None:
            raise forms.ValidationError(
                "No JSON file was provided."
            )

        try:
            uploaded_file.seek(0)
            raw_data = uploaded_file.read()

            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode("utf-8")

            data = json.loads(raw_data)

        except UnicodeDecodeError as exc:
            raise forms.ValidationError(
                "The JSON file must use UTF-8 encoding."
            ) from exc

        except json.JSONDecodeError as exc:
            raise forms.ValidationError(
                f"Invalid JSON format: {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise forms.ValidationError(
                "JSON root must be an object."
            )

        return data


class CatalogSearchForm(forms.Form):
    keyword = forms.CharField(
        required=False,
        label="Keyword",
        widget=forms.TextInput(
            attrs={"placeholder": "Search projects, developers, locations..."}
        ),
    )
    developer = forms.ChoiceField(required=False, label="Developer")
    project = forms.ChoiceField(required=False, label="Project")
    project_type = forms.ChoiceField(required=False, label="Project type")
    property_type = forms.ChoiceField(required=False, label="Property type")
    min_budget = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=18,
        decimal_places=2,
        label="Minimum budget",
    )
    max_budget = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=18,
        decimal_places=2,
        label="Maximum budget",
    )
    locality = forms.CharField(required=False, label="Locality")
    city = forms.CharField(required=False, label="City")
    district = forms.CharField(required=False, label="District")
    state = forms.CharField(required=False, label="State")
    pincode = forms.CharField(required=False, label="PIN code")
    location = forms.CharField(required=False, widget=forms.HiddenInput)
    bhk = forms.ChoiceField(required=False, label="BHK / bedrooms")
    facing = forms.ChoiceField(required=False, label="Facing")
    status = forms.ChoiceField(required=False, label="Project status")
    availability = forms.ChoiceField(required=False, label="Availability")
    possession = forms.CharField(required=False, label="Possession")
    min_area = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=14,
        decimal_places=2,
        label="Minimum area (sq. ft.)",
    )
    max_area = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=14,
        decimal_places=2,
        label="Maximum area (sq. ft.)",
    )
    amenity = forms.MultipleChoiceField(
        required=False,
        label="Amenities",
        widget=forms.SelectMultiple(attrs={"size": 4}),
    )
    feature = forms.MultipleChoiceField(
        required=False,
        label="Features",
        widget=forms.SelectMultiple(attrs={"size": 4}),
    )
    notes = forms.CharField(required=False, label="Project / configuration notes")
    min_price_per_sqft = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=14,
        decimal_places=2,
        label="Minimum price / sq. ft.",
    )
    max_price_per_sqft = forms.DecimalField(
        required=False,
        min_value=0,
        max_digits=14,
        decimal_places=2,
        label="Maximum price / sq. ft.",
    )

    def __init__(self, *args, catalog: PropertyCatalog, **kwargs):
        super().__init__(*args, **kwargs)
        developers = catalog.developers.order_by("name", "pk")
        projects = CatalogProject.objects.filter(
            developer__catalog=catalog
        ).order_by("name", "pk")
        configurations = CatalogConfiguration.objects.filter(
            project__developer__catalog=catalog
        )

        self.fields["developer"].choices = [
            ("", "All developers"),
            *((str(item.pk), item.name) for item in developers),
        ]
        self.fields["project"].choices = [
            ("", "All projects"),
            *((str(item.pk), item.name) for item in projects),
        ]
        self.fields["project_type"].choices = self._value_choices(
            projects.values_list("project_type", flat=True),
            "All project types",
        )
        self.fields["status"].choices = self._value_choices(
            projects.values_list("status", flat=True),
            "All statuses",
        )
        self.fields["availability"].choices = self._value_choices(
            configurations.values_list("availability", flat=True),
            "All availability",
        )

        property_type_choices = list(CatalogConfiguration.PROPERTY_TYPE_CHOICES)
        property_type_choices.extend(
            self._saved_choice_values(
                configurations.values_list("property_type", flat=True),
                property_type_choices,
            )
        )
        self.fields["property_type"].choices = [
            ("", "All property types"),
            *property_type_choices,
        ]

        facing_choices = list(CatalogConfiguration.FACING_CHOICES)
        facing_choices.extend(
            self._saved_choice_values(
                configurations.values_list("facing", flat=True),
                facing_choices,
            )
        )
        self.fields["facing"].choices = [
            ("", "Any facing"),
            *facing_choices,
        ]

        bhk_values = configurations.values_list("bhk", "bedrooms").distinct()
        bhk_choices = {}
        for bhk_value, bedrooms in bhk_values:
            if bedrooms is not None:
                bhk_choices[f"bedrooms:{bedrooms}"] = f"{bedrooms} BHK"
            if bhk_value:
                standard_match = re.fullmatch(
                    r"\s*(\d+)\s*(?:BHK)?\s*",
                    bhk_value,
                    re.IGNORECASE,
                )
                if standard_match:
                    number = standard_match.group(1)
                    bhk_choices[f"bedrooms:{number}"] = f"{number} BHK"
                else:
                    bhk_choices[f"bhk:{bhk_value}"] = bhk_value
        self.fields["bhk"].choices = [
            ("", "Any configuration"),
            *sorted(bhk_choices.items(), key=lambda item: item[1].casefold()),
        ]

        amenity_values = set()
        for value in configurations.values_list("amenities", flat=True):
            amenity_values.update(self._strings(value))
        amenity_values.update(
            catalog.developers.filter(
                projects__amenities__isnull=False
            ).values_list("projects__amenities__name", flat=True)
        )
        self.fields["amenity"].choices = [
            *((value, value) for value in sorted(amenity_values, key=str.casefold)),
        ]
        feature_values = set()
        for value in configurations.values_list("features", flat=True):
            feature_values.update(self._strings(value))
        feature_values.update(
            catalog.developers.filter(
                projects__highlights__isnull=False
            ).values_list("projects__highlights__text", flat=True)
        )
        self.fields["feature"].choices = [
            *((value, value) for value in sorted(feature_values, key=str.casefold)),
        ]

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "catalog-search-control")

    @staticmethod
    def _value_choices(values, empty_label):
        saved_values = sorted({value for value in values if value}, key=str.casefold)
        return [
            ("", empty_label),
            *((value, value.replace("_", " ").title()) for value in saved_values),
        ]

    @staticmethod
    def _saved_choice_values(values, existing_choices):
        existing_values = {value for value, _label in existing_choices}
        saved_values = sorted(
            {value for value in values if value and value not in existing_values},
            key=str.casefold,
        )
        return [(value, value.replace("_", " ").title()) for value in saved_values]

    @classmethod
    def _strings(cls, value):
        if isinstance(value, str):
            if value.strip():
                yield value.strip()
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from cls._strings(item)
        elif isinstance(value, dict):
            for item in value.values():
                yield from cls._strings(item)

    def clean(self):
        cleaned_data = super().clean()
        for minimum, maximum, label in (
            ("min_budget", "max_budget", "budget"),
            ("min_area", "max_area", "area"),
            ("min_price_per_sqft", "max_price_per_sqft", "price per square foot"),
        ):
            lower = cleaned_data.get(minimum)
            upper = cleaned_data.get(maximum)
            if lower is not None and upper is not None and lower > upper:
                self.add_error(maximum, f"Maximum {label} must be greater than or equal to minimum {label}.")
        return cleaned_data


class CatalogDeveloperForm(forms.ModelForm):
    class Meta:
        model = CatalogDeveloper
        fields = (
            "name",
            "developer_type",
            "contact_person",
            "phone",
            "email",
            "website",
        )


class CatalogProjectForm(forms.ModelForm):
    class Meta:
        model = CatalogProject
        fields = (
            "name",
            "project_type",
            "status",
            "total_land_area",
            "total_towers",
            "total_floors",
            "total_units",
            "starting_price",
            "price_per_sqft",
            "channel_partner_notes",
        )
        widgets = {
            "channel_partner_notes": forms.Textarea(attrs={"rows": 3}),
        }


class CatalogConfigurationForm(forms.ModelForm):
    amenities = forms.CharField(
        required=False,
        help_text="Enter one amenity per line or separate items with commas.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    features = forms.CharField(
        required=False,
        help_text="Enter one feature per line or separate items with commas.",
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta:
        model = CatalogConfiguration
        exclude = ("project",)
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_amenities(self):
        return self._parse_list(self.cleaned_data.get("amenities", ""))

    def clean_features(self):
        return self._parse_list(self.cleaned_data.get("features", ""))

    @staticmethod
    def _parse_list(value):
        return [
            item.strip()
            for item in value.replace(",", "\n").splitlines()
            if item.strip()
        ]
