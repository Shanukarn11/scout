from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('registration.urls')),
    path('coach/', include('registration.coachurls')),
    path('dashboard/', include('dashboard.urls')),
    path('login/', include('login.urls')),
    path('coachlogin/', include('coachlogin.urls')),
    path('teams/', include('teams.urls')),

]
