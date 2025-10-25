from django.apps import AppConfig

class PerfumeApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'perfume_api'
def ready(self):
    from .models import Tipo
    tipos = ["Eau Fraîche", "Eau de Cologne", "Eau de Toilette", "Eau de Parfum", "Perfume"]
    for t in tipos:
        Tipo.objects.get_or_create(nombre=t)
