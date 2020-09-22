from django.db import models

class Turnier(models.Model):
    veranstalter_id = models.IntegerField()
    turnier_id      = models.IntegerField(unique=True)
    abgeschlossen   = models.BooleanField(default=False)

class TeilnehmerListe(models.Model):
    turnier_id  = models.ForeignKey(Turnier, on_delete=models.CASCADE)
    player_id   = models.CharField(max_length=15)
    licence_nr  = models.BigIntegerField()
    lastname    = models.CharField(max_length=250)
    club_name   = models.CharField(max_length=250)
    sex         = models.BooleanField()
    ttr         = models.PositiveSmallIntegerField()
    internal_nr = models.CharField(max_length=25)
    firstname   = models.CharField(max_length=250)
    club_nr     = models.IntegerField()
    birthyear   = models.PositiveSmallIntegerField()
    verband     = models.CharField(max_length=25)
    aufgehoert  = models.IntegerField(null=True)

class Turnierspiele(models.Model):
    turnier_id  = models.ForeignKey(Turnier, on_delete=models.CASCADE)
    player1     = models.CharField(max_length=15)
    player2     = models.CharField(max_length=15)
    satz1       = models.CharField(max_length=3,null=True)
    satz2       = models.CharField(max_length=3,null=True)
    satz3       = models.CharField(max_length=3,null=True)
    satz4       = models.CharField(max_length=3,null=True)
    satz5       = models.CharField(max_length=3,null=True)
    runde       = models.SmallIntegerField(null=True)