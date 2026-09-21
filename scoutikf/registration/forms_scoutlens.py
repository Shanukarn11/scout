import re
from datetime import date

from django import forms

from .models_scoutlens import ScoutLens, ScoutLensPosition, ScoutLensToBeNotifiedPlayer


class ScoutLensRegistrationForm(forms.ModelForm):
    affiliate_code = forms.CharField(
        max_length=80,
        required=False,
        widget=forms.HiddenInput(),
    )
    mobile = forms.CharField(
        max_length=16,
        widget=forms.TextInput(attrs={
            "autocomplete": "tel",
            "inputmode": "numeric",
            "placeholder": "10-digit mobile number",
        }),
    )

    class Meta:
        model = ScoutLens
        fields = ("player_name", "mobile", "position", "dob")
        widgets = {
            "player_name": forms.TextInput(attrs={"autocomplete": "name", "placeholder": "Player full name"}),
            "position": forms.Select(choices=(("", "Select playing position"), *ScoutLensPosition.choices)),
            "dob": forms.DateInput(attrs={"type": "date", "autocomplete": "bday"}),
        }

    def clean_player_name(self):
        name = " ".join(self.cleaned_data["player_name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Enter the player's full name.")
        return name

    def clean_mobile(self):
        digits = re.sub(r"\D", "", self.cleaned_data["mobile"])
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        if not re.fullmatch(r"[6-9][0-9]{9}", digits):
            raise forms.ValidationError("Enter a valid 10-digit Indian mobile number.")
        return digits

    def clean_dob(self):
        dob = self.cleaned_data["dob"]
        today = date.today()
        if dob >= today:
            raise forms.ValidationError("Date of birth must be in the past.")
        if dob.year < today.year - 100:
            raise forms.ValidationError("Enter a valid date of birth.")
        return dob

    def clean_affiliate_code(self):
        return self.cleaned_data.get("affiliate_code", "").strip().upper()


class ScoutLensNotifyForm(forms.ModelForm):
    whatsapp_number = forms.CharField(max_length=16)

    class Meta:
        model = ScoutLensToBeNotifiedPlayer
        fields = ("name", "whatsapp_number", "position")

    def clean_name(self):
        name = " ".join(self.cleaned_data["name"].split())
        if len(name) < 2:
            raise forms.ValidationError("Enter your name.")
        return name

    def clean_whatsapp_number(self):
        digits = re.sub(r"\D", "", self.cleaned_data["whatsapp_number"])
        if len(digits) == 12 and digits.startswith("91"):
            digits = digits[2:]
        if not re.fullmatch(r"[6-9][0-9]{9}", digits):
            raise forms.ValidationError("Enter a valid 10-digit Indian WhatsApp number.")
        return digits
