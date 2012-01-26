from django.contrib import admin
from models import FirstName, NickName, LastName


class FirstNameAdmin(admin.ModelAdmin):
    pass

admin.site.register(FirstName, FirstNameAdmin)


class NickNameAdmin(admin.ModelAdmin):
    pass

admin.site.register(NickName, NickNameAdmin)


class LastNameAdmin(admin.ModelAdmin):
    pass

admin.site.register(LastName, LastNameAdmin)
