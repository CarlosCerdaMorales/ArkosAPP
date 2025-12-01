from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Tu nombre de usuario"}),
    )
    first_name = forms.CharField(
        label="Nombre",
        max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Tu nombre"}),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Tus apellidos"}),
    )
    phone_number = forms.CharField(
        label="Teléfono",
        max_length=20,
        widget=forms.TextInput(attrs={"placeholder": "Tu número de teléfono"}),
    )
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={"placeholder": "Tu correo electrónico"}),
    )
    address = forms.CharField(
        label="Dirección",
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Tu dirección"}),
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Crea una contraseña"}),
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Repite la contraseña"}),
    )
    terms_confirmed = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        label="Acepto los Términos y Condiciones",
        error_messages={'required': 'Debes aceptar los términos para continuar.'}
    )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "email",
            "address",
            "password1",
            "password2",
            "terms_confirmed",
        ]


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Nombre de usuario",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Tu nombre de usuario"}),
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"placeholder": "Tu contraseña"}),
    )


class ProfileForm(forms.ModelForm):
    first_name = forms.RegexField(
        regex=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$", max_length=150, required=True
    )
    last_name = forms.RegexField(
        regex=r"^[A-Za-zÁÉÍÓÚáéíóúÑñ\s]+$", max_length=150, required=True
    )
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
