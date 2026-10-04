from django import forms

from accounts.models import User
from bloodbank.models import BloodRequest


class ReservationForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    note = forms.CharField(
        required=False,
        max_length=255,
        label="Note (optional)",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )


class BloodRequestForm(forms.Form):
    blood_group = forms.ChoiceField(
        choices=[("", "Select blood group")] + User.BLOOD_GROUPS,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    units = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        label="Units required",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    hospital_name = forms.CharField(
        max_length=150,
        label="Hospital name",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    urgency = forms.ChoiceField(
        choices=BloodRequest.Urgency.choices,
        initial=BloodRequest.Urgency.NORMAL,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    note = forms.CharField(
        required=False,
        max_length=255,
        label="Note (optional)",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )