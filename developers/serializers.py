from rest_framework import serializers

from .models import Developer


class DeveloperSerializer(serializers.ModelSerializer):

    class Meta:
        model = Developer
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
        )