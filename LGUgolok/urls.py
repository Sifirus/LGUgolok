"""
URL configuration for LGUgolok project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core.views import no_access, page_not_found

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('core.urls')),
    path('', include('admin_panel.urls')),
    path('', include('booking.urls')),
    path('', include('equipment.urls')),
    path('', include('rooms.urls')),
    path('', include('approval.urls')),
    path('', include('notifications.urls')),
    path('', include('reports.urls')),
]

handler403 = no_access
handler404 = page_not_found
