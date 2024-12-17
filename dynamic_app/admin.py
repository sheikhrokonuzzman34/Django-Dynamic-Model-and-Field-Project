from django.contrib import admin

# Register your models here.

from dynamic_app.models import *

admin.site.register(DynamicModelInstance)
admin.site.register(DynamicModel)
admin.site.register(DynamicField)
admin.site.register(DynamicFieldChoice)

