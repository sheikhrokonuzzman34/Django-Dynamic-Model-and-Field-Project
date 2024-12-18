# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json  
import os   
    
    
# Validator for file types
def validate_file_type(value):
    allowed_extensions = ['.docx', '.csv', '.pdf']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(f"Unsupported file type. Allowed types are: {', '.join(allowed_extensions)}")


class DynamicModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


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
    ]

    dynamic_model = models.ForeignKey(DynamicModel, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=True)
    is_readonly = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order']
        unique_together = ['dynamic_model', 'name']

    def clean(self):
        if self.field_type == 'file' and self.is_unique:
            raise ValidationError("File fields cannot be marked as unique.")

    def __str__(self):
        return f"{self.dynamic_model.name} - {self.name}"


class DynamicFieldChoice(models.Model):
    dynamic_field = models.ForeignKey(DynamicField, on_delete=models.CASCADE, related_name='choices')
    value = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.display_name


class DynamicFieldFile(models.Model):
    instance = models.ForeignKey('DynamicModelInstance', on_delete=models.CASCADE, related_name='files')
    field = models.ForeignKey(DynamicField, on_delete=models.CASCADE)
    file = models.FileField(upload_to='dynamic_files/', validators=[validate_file_type])
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.instance} - {self.field.name}"


class DynamicModelInstance(models.Model):
    dynamic_model = models.ForeignKey(DynamicModel, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    data = models.JSONField()

    def clean(self):
        errors = {}
        fields = self.dynamic_model.fields.all()

        for field in fields:
            value = self.data.get(field.name)

            if field.is_required and not value:
                errors[field.name] = 'This field is required.'

            if field.field_type == 'choice' and value:
                valid_choices = field.choices.values_list('value', flat=True)
                if value not in valid_choices:
                    errors[field.name] = f"Invalid choice: {value}. Valid choices are: {', '.join(valid_choices)}."

            if value and field.is_unique:
                if DynamicModelInstance.objects.filter(
                    dynamic_model=self.dynamic_model,
                    data__contains={field.name: value}
                ).exclude(pk=self.pk).exists():
                    errors[field.name] = 'This value must be unique.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.dynamic_model.name} Instance - {self.pk}"    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    
    
    