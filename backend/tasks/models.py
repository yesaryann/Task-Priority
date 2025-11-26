from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Task(models.Model):
    """Task model for storing task information."""
    title = models.CharField(max_length=200)
    due_date = models.DateField(null=True, blank=True)
    estimated_hours = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0)])
    importance = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    dependencies = models.JSONField(default=list, blank=True)  # List of task IDs
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        """Validate the model instance."""
        from django.core.exceptions import ValidationError
        
        # Ensure importance is within valid range
        if self.importance < 1 or self.importance > 10:
            raise ValidationError({'importance': 'Importance must be between 1 and 10.'})
        
        # Ensure estimated_hours is positive if provided
        if self.estimated_hours is not None and self.estimated_hours < 0:
            raise ValidationError({'estimated_hours': 'Estimated hours must be non-negative.'})

    class Meta:
        ordering = ['-created_at']

