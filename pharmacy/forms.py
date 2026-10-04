from django import forms

from .models import Medicine


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ["name", "category", "description", "price", "quantity"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Pain relief"}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.01", "min": "0"}
            ),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }
        labels = {"price": "Price (₹)", "quantity": "Stock quantity"}

    def clean_price(self):
        price = self.cleaned_data["price"]
        if price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price