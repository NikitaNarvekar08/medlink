from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class StyledFormMixin:
    """Adds Bootstrap classes to every field."""

    def style_fields(self):
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)


class RegisterForm(StyledFormMixin, UserCreationForm):
    role = forms.ChoiceField(
        choices=[(v, l) for v, l in User.Role.choices if v != User.Role.ADMIN],
        label="Register as",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username", "email", "role", "phone", "city", "address",
            "organization_name", "license_number", "blood_group",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["phone"].required = True
        self.fields["city"].required = True
        self.style_fields()

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        if role in (User.Role.PHARMACY, User.Role.BLOODBANK):
            for name in ("organization_name", "license_number"):
                if not cleaned.get(name):
                    self.add_error(name, "Required for pharmacies and blood banks.")
        if role == User.Role.DONOR and not cleaned.get("blood_group"):
            self.add_error("blood_group", "Blood group is required for donors.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        # Pharmacies and blood banks must be verified by the admin
        user.is_verified = user.role in (User.Role.PATIENT, User.Role.DONOR)
        if commit:
            user.save()
        return user


class LoginForm(StyledFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()