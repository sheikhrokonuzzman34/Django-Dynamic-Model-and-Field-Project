from django import forms
from .models import *
from django.core.exceptions import ValidationError

class DynamicModelForm(forms.ModelForm):
    class Meta:
        model = DynamicModel
        fields = ['name']  # 'created_by' will be set in the view

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set 'created_by' as hidden in the form (it won't appear in the form fields)
        self.fields['created_by'] = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if DynamicModel.objects.filter(name=name).exists():
            raise ValidationError("A dynamic model with this name already exists.")
        return name


class DynamicFieldForm(forms.ModelForm):
    class Meta:
        model = DynamicField
        fields = [
            'dynamic_model', 'name', 'display_name', 'field_type',
            'is_required', 'is_unique', 'is_readonly', 'display_order'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dynamic_model'].queryset = DynamicModel.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        is_unique = cleaned_data.get('is_unique')

        if field_type == 'file' and is_unique:
            raise ValidationError("File fields cannot be marked as unique.")

        return cleaned_data

    def save(self, commit=True):
        field = super().save(commit=False)
        if commit:
            field.created_by = self.initial.get('created_by')
            field.save()
        return field

  


class DynamicModelInstanceForm(forms.ModelForm):
    class Meta:
        model = DynamicModelInstance
        fields = ['dynamic_model', 'data']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        dynamic_model = kwargs.get('instance').dynamic_model if kwargs.get('instance') else None
        if dynamic_model:
            fields = dynamic_model.fields.all()
            for field in fields:
                if field.field_type == 'bool':
                    self.fields[field.name] = forms.BooleanField(required=field.is_required)
                elif field.field_type == 'char':
                    self.fields[field.name] = forms.CharField(required=field.is_required, max_length=255)
                elif field.field_type == 'text':
                    self.fields[field.name] = forms.CharField(required=field.is_required, widget=forms.Textarea)
                elif field.field_type == 'int':
                    self.fields[field.name] = forms.IntegerField(required=field.is_required)
                elif field.field_type == 'decimal':
                    self.fields[field.name] = forms.DecimalField(required=field.is_required)
                elif field.field_type == 'date':
                    self.fields[field.name] = forms.DateField(required=field.is_required)
                elif field.field_type == 'datetime':
                    self.fields[field.name] = forms.DateTimeField(required=field.is_required)
                elif field.field_type == 'file':
                    self.fields[field.name] = forms.FileField(required=field.is_required)
                elif field.field_type == 'choice':
                    # Fetch choices dynamically
                    choices = [(choice.value, choice.display_name) for choice in field.choices.all()]
                    self.fields[field.name] = forms.ChoiceField(choices=choices, required=field.is_required)

    def clean(self):
        cleaned_data = super().clean()
        dynamic_model = self.cleaned_data.get('dynamic_model')

        if dynamic_model:
            fields = dynamic_model.fields.all()
            errors = {}

            for field in fields:
                value = cleaned_data.get(field.name)

                # Required validation
                if field.is_required and not value:
                    errors[field.name] = 'This field is required.'

                # Unique validation
                if field.is_unique and value:
                    if DynamicModelInstance.objects.filter(
                        dynamic_model=dynamic_model,
                        data__contains={field.name: value}
                    ).exclude(pk=self.instance.pk).exists():
                        errors[field.name] = 'This value must be unique.'

            if errors:
                raise ValidationError(errors)

        return cleaned_data    
    
    
class DynamicFieldChoiceForm(forms.ModelForm):
    class Meta:
        model = DynamicFieldChoice
        fields = ['value', 'display_name']
        
        
class DynamicFieldFileForm(forms.ModelForm):
    class Meta:
        model = DynamicFieldFile
        fields = ['file']        
    
