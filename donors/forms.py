from django import forms

from accounts.models import User
from accounts.validators import validate_city, validate_phone


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
        for name in ("phone", "city", "address", "blood_group"):
            self.fields[name].required = True
            self.fields[name].error_messages["required"] = (
                f"{self.fields[name].label} is required."
            )
        self.fields["phone"].validators.append(validate_phone)
        self.fields["city"].validators.append(validate_city)
        self.fields["phone"].widget.attrs.update(
            {
                "maxlength": "10",
                "minlength": "10",
                "pattern": "[0-9]{10}",
                "inputmode": "numeric",
                "title": "Enter exactly 10 digits (numbers only)",
            }
        )