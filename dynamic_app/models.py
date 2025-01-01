
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import json
import os

# Custom validation to ensure uploaded file types are supported
def validate_file_type(value):
    allowed_extensions = ['.docx', '.csv', '.pdf']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")

# Represents a dynamic model schema created by users
class DynamicModel(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Unique name for the dynamic model
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # User who created the model
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp for the last update

    def __str__(self):
        return self.name

# Represents individual fields within a DynamicModel
class DynamicField(models.Model):
    FIELD_TYPES = [
        ('char', 'Character'),
        ('text', 'Text'),
        ('int', 'Integer'),
        ('decimal', 'Decimal'),
        ('bool', 'Boolean'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('file', 'File'),
        ('choice', 'Choice'),
        ('fk', 'Foreign Key'),
        ('m2m', 'Many to Many'),
    ]

    dynamic_model = models.ForeignKey(DynamicModel, on_delete=models.CASCADE, related_name='fields')  # Link to the parent dynamic model
    name = models.CharField(max_length=100)  # Internal name of the field
    display_name = models.CharField(max_length=100)  # User-facing name for display purposes
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)  # Type of the field
    is_required = models.BooleanField(default=False)  # Marks the field as mandatory
    is_unique = models.BooleanField(default=True)  # Ensures uniqueness of field values
    is_readonly = models.BooleanField(default=False)  # Marks the field as read-only
    display_order = models.IntegerField(default=0)  # Order in which the field should be displayed
    related_model = models.ForeignKey(DynamicModel, null=True, blank=True, 
                                      on_delete=models.SET_NULL, related_name='related_fields')  # For relational fields
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # User who created the field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order']  # Fields should be ordered by display_order
        unique_together = ['dynamic_model', 'name']  # Enforces unique field names within a model

    # Custom validation logic for DynamicField
    def clean(self):
        if self.field_type == 'file' and self.is_unique:
            raise ValidationError("File fields cannot be marked as unique.")

    def __str__(self):
        return f"{self.dynamic_model.name} - {self.name}"

# Represents choices for fields of type 'choice'
class DynamicFieldChoice(models.Model):
    dynamic_field = models.ForeignKey(DynamicField, on_delete=models.CASCADE, related_name='choices')  # Field associated with this choice
    value = models.CharField(max_length=255)  # Value stored in the database
    display_name = models.CharField(max_length=255)  # User-facing display value
    order = models.IntegerField(default=0)  # Order of the choice for display purposes

    class Meta:
        ordering = ['order']  # Choices should be ordered by the 'order' field

    def __str__(self):
        return self.display_name

# Generates a file upload path based on model and field information
def file_upload_path(instance, filename):
    return f'dynamic_files/{instance.instance.dynamic_model.name}/{instance.field.name}/{filename}'

# Represents file uploads for dynamic fields
class DynamicFieldFile(models.Model):
    instance = models.ForeignKey('DynamicModelInstance', on_delete=models.CASCADE, related_name='files')  # Associated instance
    field = models.ForeignKey(DynamicField, on_delete=models.CASCADE)  # Field associated with the file
    file = models.FileField(upload_to=file_upload_path, validators=[validate_file_type])  # Uploaded file
    file_name = models.CharField(max_length=255)  # Name of the file
    file_extension = models.CharField(max_length=10)  # Extension of the file
    uploaded_at = models.DateTimeField(auto_now_add=True)  # Timestamp of the upload

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_file = self.file if self.pk else None

    def save(self, *args, **kwargs):
        if self.file:
            # Extract filename without path
            filename = os.path.basename(self.file.name)
            # Set file_name and file_extension
            self.file_name = os.path.splitext(filename)[0]
            self.file_extension = os.path.splitext(filename)[1].lower()
            
            # Handle file replacement
            if self.pk and self._original_file and self._original_file != self.file:
                # Delete old file if it's being replaced
                self._original_file.delete(save=False)
        
        super().save(*args, **kwargs)
        # Update the reference to the current file
        self._original_file = self.file

    def delete(self, *args, **kwargs):
        # Delete the actual file when the model instance is deleted
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"File for {self.instance} - {self.field.name}"
    
    
# Represents an instance of a DynamicModel with its data
class DynamicModelInstance(models.Model):
    dynamic_model = models.ForeignKey(DynamicModel, on_delete=models.CASCADE)  # Link to the parent dynamic model
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # User who created the instance
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data = models.JSONField()  # Stores field values as JSON

    # Custom validation logic for instance data
    def clean(self):
        errors = {}
        fields = self.dynamic_model.fields.all()

        for field in fields:
            value = self.data.get(field.name)

            if field.is_required and not value and field.field_type != 'file':
                errors[field.name] = 'This field is required.'

            if field.field_type == 'choice' and value:
                valid_choices = field.choices.values_list('value', flat=True)
                if value not in valid_choices:
                    errors[field.name] = f"Invalid choice: {value}. Valid choices are: {', '.join(valid_choices)}."

            if value and field.is_unique and field.field_type != 'file':
                if DynamicModelInstance.objects.filter(
                    dynamic_model=self.dynamic_model,
                    data__contains={field.name: value}
                ).exclude(pk=self.pk).exists():
                    errors[field.name] = 'This value must be unique.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.dynamic_model.name} Instance - {self.pk}"
    
    
    
    
    
    
    