from django.contrib import admin
from wikipbx.wikipbxweb import models

for model in models.__all__:
    admin.site.register(getattr(models, model))


