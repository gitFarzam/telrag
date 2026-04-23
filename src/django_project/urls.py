from django.conf import settings  
from django.conf.urls.static import static  
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chat.urls')),
    path('', include('django_prometheus.urls')),
]
# Serve static and media files during development  
if settings.DEBUG:  
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# routing 404 handler
handler404 = 'chat.views.redirect_404'