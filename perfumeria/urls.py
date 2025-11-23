# perfumeria/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from rest_framework_simplejwt.views import TokenRefreshView
from perfume_api.views_auth import CustomTokenObtainPairView

# ==================== REDIRECCIÓN A ADMIN ====================
def home_redirect(request):
    """Redirige la raíz al admin"""
    return redirect('/admin/')

# ==================== URLS PRINCIPALES ====================
urlpatterns = [
    # 🏠 Redirección raíz
    path('', home_redirect, name='home'),
    
    # 🔐 Admin de Django
    path('admin/', admin.site.urls),
    
    # 🔑 Autenticación JWT
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 📦 API completa (incluye dashboard en api/admin/dashboard/)
    path('api/', include('perfume_api.urls')),
]

# ==================== ARCHIVOS ESTÁTICOS Y MEDIA ====================
if settings.DEBUG:
    # 📂 Servir archivos multimedia en desarrollo
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # 📂 Servir archivos estáticos en desarrollo
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
