from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User
from .validators import validate_city, validate_email_strict, validate_phone


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

        # Details every user must fill in
        for name in ("email", "phone", "city", "address"):
            self.fields[name].required = True

        # Friendlier "missing field" messages
        for field in self.fields.values():
            field.error_messages["required"] = f"{field.label} is required."

        # Validation rules
        self.fields["email"].validators = [validate_email_strict]
        self.fields["phone"].validators.append(validate_phone)
        self.fields["city"].validators.append(validate_city)

        self.style_fields()

        # Browser-side hints (pop-up messages)
        self.fields["email"].widget.attrs.update(
            {"placeholder": "name@example.com"}
        )
        self.fields["phone"].widget.attrs.update(
            {
                "maxlength": "10",
                "minlength": "10",
                "pattern": "[0-9]{10}",
                "inputmode": "numeric",
                "title": "Enter exactly 10 digits (numbers only)",
                "placeholder": "10-digit mobile number",
            }
        )

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
        self.fields["username"].error_messages["required"] = "Please enter your username."
        self.fields["password"].error_messages["required"] = "Please enter your password."
        self.style_fields()