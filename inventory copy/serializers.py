from rest_framework import serializers

from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(
        source="project.name",
        read_only=True,
    )

    class Meta:
        model = Inventory
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )