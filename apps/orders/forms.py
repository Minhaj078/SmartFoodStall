from django import forms
from django.utils import timezone
from .models import Order, BREAK_SLOT_CHOICES


class OrderForm(forms.ModelForm):
    break_slot = forms.ChoiceField(choices=BREAK_SLOT_CHOICES, widget=forms.RadioSelect)
    pickup_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date().isoformat()}),
        initial=timezone.now().date
    )
    special_instructions = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any special instructions (optional)'}),
        required=False
    )

    class Meta:
        model = Order
        fields = ['break_slot', 'pickup_date', 'special_instructions']

    def clean_pickup_date(self):
        pickup_date = self.cleaned_data['pickup_date']
        today = timezone.now().date()
        if pickup_date < today:
            raise forms.ValidationError("Pickup date cannot be in the past.")
        return pickup_date
