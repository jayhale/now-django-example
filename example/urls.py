from django.urls import path
from django.contrib import admin
from example.views import index


urlpatterns = [
    path('admin/',admin.site.urls),
    path('', index),
]
