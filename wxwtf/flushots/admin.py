from django.contrib import admin
from models import FreeFluVaccine


class FreeFluVaccineAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'date', 'time_range',]
    list_editable = ['address', 'time_range']
    
admin.site.register(FreeFluVaccine, FreeFluVaccineAdmin)
