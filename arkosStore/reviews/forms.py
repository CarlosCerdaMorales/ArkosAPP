from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=[(i, i) for i in range(1, 6)],
        widget=forms.RadioSelect(attrs={'class': 'star-rating'}),
        label='Calificación'
    )
    
    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Cuéntanos sobre tu experiencia (opcional)',
            'rows': 5,
            'maxlength': 500
        }),
        label='Comentario',
        max_length=500
    )

    class Meta:
        model = Review
        fields = ['rating', 'comment']
