from rest_framework import serializers
from .models import Task


class TaskAnalyzeSerializer(serializers.Serializer):
    """Serializer for task input validation."""
    id = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField(required=True, max_length=200)
    due_date = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.FloatField(required=False, allow_null=True, min_value=0)
    importance = serializers.IntegerField(required=False, default=5, min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list
    )
    
    def validate_importance(self, value):
        """Ensure importance is within valid range."""
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError("Importance must be between 1 and 10.")
        return value or 5
    
    def validate_estimated_hours(self, value):
        """Ensure estimated_hours is non-negative."""
        if value is not None and value < 0:
            raise serializers.ValidationError("Estimated hours must be non-negative.")
        return value


class TaskSerializer(serializers.Serializer):
    """Serializer for task output with calculated score."""
    id = serializers.CharField(required=False, allow_null=True)
    title = serializers.CharField()
    due_date = serializers.DateField(allow_null=True)
    estimated_hours = serializers.FloatField(allow_null=True)
    importance = serializers.IntegerField()
    dependencies = serializers.ListField(child=serializers.CharField(), allow_empty=True)
    priority_score = serializers.FloatField()
    explanation = serializers.CharField()
    has_circular_dependency = serializers.BooleanField(default=False)
    circular_dependency_chain = serializers.ListField(
        child=serializers.ListField(child=serializers.CharField()),
        required=False,
        allow_empty=True
    )

