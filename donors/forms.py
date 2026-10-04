from django import forms

from accounts.models import User


class DonorProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["phone", "city", "address", "blood_group", "is_available"]
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "blood_group": forms.Select(attrs={"class": "form-select"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {"is_available": "I am available to donate"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].required = True
        self.fields["city"].required = True
        self.fields["blood_group"].required = True