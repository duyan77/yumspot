# admin.py

from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import User


@admin.register(User)
class CustomAdminClass(ModelAdmin):
	pass
