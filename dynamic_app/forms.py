from django import forms
from .models import DynamicModel, DynamicField, DynamicModelInstance
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
        fields = ['dynamic_model', 'name', 'display_name', 'field_type', 'is_required', 
                  'is_unique', 'is_readonly', 'default_value', 'display_order', 'related_model', 'field_options']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dynamic_model'].queryset = DynamicModel.objects.all()
        self.fields['related_model'].queryset = DynamicModel.objects.all()

    def clean_name(self):
        name = self.cleaned_data.get('name')
        dynamic_model = self.cleaned_data.get('dynamic_model')
        
        if DynamicField.objects.filter(dynamic_model=dynamic_model, name=name).exists():
            raise ValidationError(f"Field with name '{name}' already exists in this dynamic model.")
        
        return name

    def clean_field_type(self):
        field_type = self.cleaned_data.get('field_type')
        if field_type == 'fk' and not self.cleaned_data.get('related_model'):
            raise ValidationError("Foreign Key type fields must have a related model.")
        return field_type


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
                    self.fields[field.name] = forms.BooleanField(required=False)
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
                elif field.field_type == 'fk':
                    self.fields[field.name] = forms.ModelChoiceField(queryset=field.related_model.objects.all(), required=field.is_required)
                elif field.field_type == 'm2m':
                    self.fields[field.name] = forms.ModelMultipleChoiceField(queryset=field.related_model.objects.all(), required=field.is_required)
                
                if field.default_value:
                    self.fields[field.name].initial = field.default_value

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
