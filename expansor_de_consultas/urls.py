from django.contrib import admin
from django.urls import path, include
from expansor import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('expansor.urls')),  # 👈 esta línea importa las URLs de la app
]