from django.contrib import admin

from .models import Appointment, Availability, Service

# Register your models here.

admin.site.register(Appointment)
admin.site.register(Availability)
admin.site.register(Service)
