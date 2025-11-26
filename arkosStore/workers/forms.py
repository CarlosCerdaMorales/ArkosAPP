from django import forms
from .models import Worker, Specialty

class WorkerForm(forms.ModelForm):
    class Meta:
        model = Worker
        fields = ["name", "specialties", "image", "bio"]
        widgets = {
            "specialties": forms.CheckboxSelectMultiple(),
            "bio": forms.Textarea(attrs={"rows": 4}),
        }
