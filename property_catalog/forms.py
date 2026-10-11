import json

from django import forms


class PropertyCatalogImportForm(forms.Form):

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


        # ==============================
        # STORE PARSED DATA
        # ==============================

        self.cleaned_data[
            "catalog_data"
        ] = data


        # Reset file pointer
        file.seek(0)


        return file




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
