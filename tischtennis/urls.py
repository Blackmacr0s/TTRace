from django.urls import path

from . import views

urlpatterns = [
    path('', views.create_turnier),
    path('<int:tourny_id>/delete/', views.delete_turnier),
    path('<int:tourny_id>/show/', views.showSpiele),
    path('<int:tourny_id>/show/runde<int:runde>/', views.show_spiele),
    path('<int:tourny_id>/tabelle/', views.show_tabelle),
    path('<int:tourny_id>/tabelle/runde<int:runde>/', views.show_tabelle),
    path('<int:tourny_id>/teilnehmer/', views.show_teilnehmer),
    path('<int:tourny_id>/teilnehmer/<int:player_id>/<int:runde>/', views.drop_teilnehmer),
    path('<int:tourny_id>/show/<int:game_id>/', views.save_partie),
    path('<int:tourny_id>/create/<int:runde>/', views.create_runde),
    path('<int:tourny_id>/auslosung/', views.create_auslosung),
    path('<int:tourny_id>/runde<int:runde>/delete/', views.delete_runde),
    path('<int:tourny_id>/show/<int:game_id>/edit/', views.delete_ergebnis_partie),
]