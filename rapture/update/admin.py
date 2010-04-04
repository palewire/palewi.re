# Admin
from django.contrib import admin

# Models
from models import UpdateLog


class UpdateLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'start_date', 'end_date', 'outcome', 'loaded_new_data',)


admin.site.register(UpdateLog, UpdateLogAdmin)
