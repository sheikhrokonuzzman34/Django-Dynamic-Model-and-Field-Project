# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import DynamicModel, DynamicField, DynamicModelInstance
from .forms import DynamicModelForm, DynamicFieldForm
import json

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
        form = DynamicFieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            field.dynamic_model = model
            field.created_by = request.user  # Assign the logged-in user
            field.save()
            messages.success(request, 'Field added successfully!')
            return redirect('model_detail', pk=model_pk)
    else:
        form = DynamicFieldForm()
    
    return render(request, 'dynamic_models/field_form.html', {
        'form': form,
        'model': model
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
        
        for field in fields:
            value = request.POST.get(field.name)
            if field.is_required and not value:
                errors[field.name] = 'This field is required.'
            data[field.name] = value
        
        if not errors:
            instance = DynamicModelInstance.objects.create(
                dynamic_model=model,
                created_by=request.user,
                data=data
            )
            messages.success(request, 'Instance created successfully!')
            return redirect('instance_list',  model_pk=model_pk)
        
        messages.error(request, 'Please correct the errors below.')
    
    return render(request, 'dynamic_models/instance_form.html', {
        'model': model,
        'fields': fields
    })
    
    
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