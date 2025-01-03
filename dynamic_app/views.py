# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import *
from .forms import *
import json
# hello 
from django.http import JsonResponse


@login_required
def model_list(request):
    models = DynamicModel.objects.filter(created_by=request.user)
    return render(request, 'dynamic_models/model_list.html', {'models': models})

@login_required
def model_create(request):
    if request.method == 'POST':
        form = DynamicModelForm(request.POST)
        if form.is_valid():
            model = form.save(commit=False)
            model.created_by = request.user
            model.save()
            messages.success(request, 'Model created successfully!')
            return redirect('model_detail', pk=model.pk)
    else:
        form = DynamicModelForm()
    
    return render(request, 'dynamic_models/model_form.html', {'form': form})

@login_required
def model_detail(request, pk):
    model = get_object_or_404(DynamicModel, pk=pk, created_by=request.user)
    fields = model.fields.all()
    instances = DynamicModelInstance.objects.filter(dynamic_model=model)
    
    return render(request, 'dynamic_models/model_detail.html', {
        'model': model,
        'fields': fields,
        'instances': instances
    })


    
@login_required
def field_create(request, model_pk):
    model = get_object_or_404(DynamicModel, pk=model_pk, created_by=request.user)

    if request.method == 'POST':
        form = DynamicFieldForm(request.POST, request.FILES, initial={
            'dynamic_model': model,
            'created_by': request.user
        })
        if form.is_valid():
            form.save()
            messages.success(request, 'Field added successfully!')
            return redirect('model_detail', pk=model_pk)
    else:
        form = DynamicFieldForm()

    return render(request, 'dynamic_models/field_form.html', {
        'form': form,
        'model': model
    })
    
@login_required
def add_field_choices(request, field_id):
    field = get_object_or_404(DynamicField, pk=field_id, created_by=request.user)
    
    if request.method == 'POST':
        form = DynamicFieldChoiceForm(request.POST)
        if form.is_valid():
            choice = form.save(commit=False)
            choice.dynamic_field = field  # Associate the choice with the field
            choice.save()
            messages.success(request, 'Choice added successfully!')
            return redirect('add_field_choices', field_id=field_id)
    else:
        form = DynamicFieldChoiceForm()
    
    choices = DynamicFieldChoice.objects.filter(dynamic_field=field)
    
    return render(request, 'dynamic_models/add_field_choices.html', {
        'form': form,
        'field': field,
        'choices': choices
    })

    

    

@login_required
def field_update(request, pk):
    field = get_object_or_404(DynamicField, pk=pk, dynamic_model__created_by=request.user)
    
    if request.method == 'POST':
        form = DynamicFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, 'Field updated successfully!')
            return redirect('model_detail', pk=field.dynamic_model.pk)
    else:
        form = DynamicFieldForm(instance=field)
    
    return render(request, 'dynamic_models/field_form.html', {
        'form': form,
        'field': field,
        'model': field.dynamic_model
    })


    
    

@login_required
def instance_create(request, model_pk):
    model = get_object_or_404(DynamicModel, pk=model_pk, created_by=request.user)
    fields = model.fields.all()

    if request.method == 'POST':
        data = {}
        errors = {}
        files_to_save = []

        for field in fields:
            if field.field_type == 'file':
                uploaded_file = request.FILES.get(field.name)
                if field.is_required and not uploaded_file:
                    errors[field.name] = 'This file is required.'
                elif uploaded_file:
                    # Validate the file type
                    try:
                        validate_file_type(uploaded_file)
                        files_to_save.append((field, uploaded_file))
                        # Include file metadata in the JSONField
                        data[field.name] = {
                            'file_name': uploaded_file.name,
                            'file_extension': os.path.splitext(uploaded_file.name)[1].lower()
                        }
                    except ValidationError as e:
                        errors[field.name] = e.messages[0]
            else:
                value = request.POST.get(field.name)
                if field.is_required and not value:
                    errors[field.name] = 'This field is required.'
                else:
                    data[field.name] = value

        if not errors:
            # Create the instance
            instance = DynamicModelInstance.objects.create(
                dynamic_model=model,
                created_by=request.user,
                data=data
            )

            # Save files linked to the instance
            for field, uploaded_file in files_to_save:
                DynamicFieldFile.objects.create(
                    instance=instance,
                    field=field,
                    file=uploaded_file,
                    file_name=uploaded_file.name,
                    file_extension=os.path.splitext(uploaded_file.name)[1].lower()
                )

            messages.success(request, 'Instance created successfully!')
            return redirect('instance_list', model_pk=model_pk)

        messages.error(request, 'Please correct the errors below.')
        return JsonResponse({"errors": errors}, status=400)

    return render(request, 'dynamic_models/instance_form.html', {
        'model': model,
        'fields': fields,
        'errors': errors if request.method == 'POST' else {}
    }) 


@login_required
def upload_file(request, instance_id, field_id):
    instance = get_object_or_404(DynamicModelInstance, pk=instance_id, created_by=request.user)
    field = get_object_or_404(DynamicField, pk=field_id)

    if request.method == 'POST':
        form = DynamicFieldFileForm(request.POST, request.FILES)
        if form.is_valid():
            file_instance = form.save(commit=False)
            file_instance.instance = instance
            file_instance.field = field
            file_instance.save()
            messages.success(request, 'File uploaded successfully!')
            return redirect('instance_detail', instance_id=instance.id)
    else:
        form = DynamicFieldFileForm()

    return render(request, 'dynamic_models/upload_file.html', {'form': form, 'instance': instance, 'field': field})    
    
    
@login_required
def instance_list(request, model_pk):
    model = get_object_or_404(DynamicModel, pk=model_pk, created_by=request.user)
    instances = DynamicModelInstance.objects.filter(dynamic_model=model)

    fields = model.fields.all()  # Get all the fields of the dynamic model
    return render(request, 'dynamic_models/instance_list.html', {
        'model': model,
        'instances': instances,
        'fields': fields,
    })    
    
    



def dynamic_instance_search(request):
    query = request.GET.get('q', '')
    results = []
    fields = []
    
    if query:
        # Fetch matching DynamicModelInstance objects
        results = DynamicModelInstance.objects.filter(
            data__icontains=query
        ).select_related('dynamic_model', 'created_by')
        
        # Get fields from the first instance's dynamic_model
        if results.exists():
            fields = results.first().dynamic_model.fields.all()

    context = {
        'query': query,
        'results': results,
        'fields': fields,
    }
    return render(request, 'dynamic_models/dynamic_instance_search.html', context)
    