# Admin
from django.contrib import admin

# Models
from kennedy.models import *


class FirstNameAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(FirstName, FirstNameAdmin)

class NickNameAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(NickName, NickNameAdmin)

class LastNameAdmin(admin.ModelAdmin):
	pass
	
admin.site.register(LastName, LastNameAdmin)