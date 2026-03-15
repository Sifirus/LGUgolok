from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('login', CustomLoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('password_reset', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password_reset/confirm/<uidb64>/<token>', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('profile', user_profile, name='profile'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)