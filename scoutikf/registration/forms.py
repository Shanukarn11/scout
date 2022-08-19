from django import forms

from .models import Upload, Uploadfile


class UploadForm(forms.ModelForm):

    class Meta:
        model = Upload
        fields = ('image','unique','fname','lname','mobilenumberupload',)
        widgets = {
            'image': forms.FileInput(attrs={'accept': "image/*"}),
            'unique': forms.TextInput(attrs={'type': "hidden"}),
            'fname':forms.TextInput(attrs={'type': "hidden"}),
            'lname':forms.TextInput(attrs={'type': "hidden"}),
            'mobilenumberupload':forms.TextInput(attrs={'type': "hidden"})
        }

class UploadfileForm(forms.ModelForm):
    class Meta:
        model = Uploadfile
        fields = ('file','unique','fname','lname','mobilenumberupload',)
        widgets = {
            'file': forms.FileInput(attrs={'accept': "image/*,"}),
            'unique': forms.TextInput(attrs={'type': "hidden"}),
            'fname':forms.TextInput(attrs={'type': "hidden"}),
            'lname':forms.TextInput(attrs={'type': "hidden"}),
            'mobilenumberupload':forms.TextInput(attrs={'type': "hidden"})
        }
