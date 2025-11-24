from django.contrib import admin

from .models import Specialty, Worker

# Register your models here.

admin.site.register(Worker)
admin.site.register(Specialty)
