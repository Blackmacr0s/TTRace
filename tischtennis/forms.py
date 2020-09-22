from django import forms

class TurnierForm(forms.Form):
    veranstalter_id = forms.CharField()
    turnier_id      = forms.CharField()
    xmldatei        = forms.CharField()

class SpieleForm(forms.Form):
    satz1 = forms.IntegerField(min_value=-99,max_value=99)
    satz2 = forms.IntegerField(min_value=-99,max_value=99)
    satz3 = forms.IntegerField(min_value=-99,max_value=99)
    satz4 = forms.IntegerField(min_value=-99,max_value=99,required=False)
    satz5 = forms.IntegerField(min_value=-99,max_value=99,required=False)