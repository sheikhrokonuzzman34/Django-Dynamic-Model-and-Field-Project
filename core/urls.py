"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from dynamic_app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', views.model_list, name='model_list'),
    path('model_create', views.model_create, name='model_create'),
    path('models/<int:pk>/', views.model_detail, name='model_detail'),
    
    path('models/<int:model_pk>/fields/create/', views.field_create, name='field_create'),
    path('fields/<int:field_id>/choices/', views.add_field_choices, name='add_field_choices'),
    path('fields/<int:pk>/update/', views.field_update, name='field_update'),
    
    path('models/<int:model_pk>/instances/', views.instance_list, name='instance_list'),
    path('models/<int:model_pk>/instances/create/', views.instance_create, name='instance_create'),
    path('instances/<int:instance_id>/fields/<int:field_id>/upload/', views.upload_file, name='upload_file'),
    
    path('search/', views.dynamic_instance_search, name='dynamic_instance_search'),

]
