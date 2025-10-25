from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from perfume_api.views_auth import CustomTokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

# 🔹 Redirección automática a /admin si se abre la raíz "/"
def home_redirect(request):
    return redirect('/admin/')

urlpatterns = [
    path('', home_redirect),  # ✅ Si entras a "/", redirige a /admin/
    path('admin/', admin.site.urls),

    # ✅ Login con JWT personalizado (devuelve token + datos de usuario)
    path('api/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    # ✅ Refresh token (para renovar tokens de acceso)
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ✅ Todas las rutas de la app principal (usuarios, marcas, productos, etc.)
    path('api/', include('perfume_api.urls')),
]

# ✅ Para servir archivos multimedia en modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
