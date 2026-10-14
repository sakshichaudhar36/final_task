from django.contrib import admin
from .models import Complaint, ComplaintHistory, Evidence

admin.site.register(Complaint)
admin.site.register(ComplaintHistory)
admin.site.register(Evidence)

# Register your models here.
