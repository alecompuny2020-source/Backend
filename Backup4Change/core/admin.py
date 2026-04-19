from django.contrib import admin
from .models import User, UserAddress, UserPreference, Otp

# Register your models here.
admin.site.register(User)
admin.site.register(UserAddress)
admin.site.register(UserPreference)
admin.site.register(Otp)
