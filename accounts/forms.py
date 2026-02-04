from django import forms
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()


class LoginForm(forms.Form):
    """Form used for user login"""

    login = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super(LoginForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        login = cleaned_data.get("login")
        password = cleaned_data.get("password")

        if login and password:
            self.user_cache = authenticate(
                self.request, login=login, password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError("請輸入正確的帳號及密碼。")
            cleaned_data["user"] = self.user_cache

        return cleaned_data


class EmailValidationForm(forms.Form):
    """Form to validate email field"""

    email = forms.EmailField()


class UsernameValidationForm(forms.Form):
    """Form to validate username field"""

    username = forms.CharField()
