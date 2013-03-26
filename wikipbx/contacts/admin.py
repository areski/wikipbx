from django.contrib import admin
from wikipbx.contacts import models

for model in models.__all__:
    admin.site.register(getattr(models, model))


