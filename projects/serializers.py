from rest_framework import serializers

from .models import Project


class ProjectSerializer(serializers.ModelSerializer):
    developer_name = serializers.CharField(
        source="developer.name",
        read_only=True,
    )

    location_name = serializers.CharField(
        source="location.name",
        read_only=True,
    )

    class Meta:
        model = Project
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )