from django.contrib import admin
from .models import Turnier,TeilnehmerListe,Turnierspiele

@admin.register(TeilnehmerListe)
class TeilnehmerListeAdmin(admin.ModelAdmin):
    pass

@admin.register(Turnier)
class TurnierAdmin(admin.ModelAdmin):
    pass

@admin.register(Turnierspiele)
class TurnierspieleAdmin(admin.ModelAdmin):
    pass