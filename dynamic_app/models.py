# models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import json

class DynamicModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
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
        ('fk', 'Foreign Key'),
        ('m2m', 'Many to Many'),
    ]

    dynamic_model = models.ForeignKey(DynamicModel, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=True)
    is_readonly = models.BooleanField(default=False)
    default_value = models.TextField(null=True, blank=True)
    display_order = models.IntegerField(default=0)
    related_model = models.ForeignKey(DynamicModel, null=True, blank=True, 
                                    on_delete=models.SET_NULL, related_name='related_fields')
    field_options = models.JSONField(default=dict, blank=True)  # For additional field configurations

    class Meta:
        ordering = ['display_order']
        unique_together = ['dynamic_model', 'name']

    def __str__(self):
        return f"{self.dynamic_model.name} - {self.name}"

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
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    

    
    
    
    