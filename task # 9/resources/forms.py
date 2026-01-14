from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Resource, Booking


class BookingForm(forms.ModelForm):
    """Form for creating a new booking."""
    
    resource = forms.ModelChoiceField(
        queryset=Resource.objects.all(),
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        }),
        empty_label="Select a resource..."
    )
    
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    class Meta:
        model = Booking
        fields = ['resource', 'start_time', 'end_time']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        resource = cleaned_data.get('resource')
        
        if start_time and end_time:
            # Ensure end_time is after start_time
            if end_time <= start_time:
                raise forms.ValidationError('End time must be after start time.')
            
            # Ensure booking is not in the past
            if start_time < timezone.now():
                raise forms.ValidationError('Cannot book resources in the past.')
            
            # Check for overlapping approved bookings
            if resource:
                overlapping = Booking.objects.filter(
                    resource=resource,
                    status='Approved',
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )
                
                if overlapping.exists():
                    overlapping_booking = overlapping.first()
                    raise forms.ValidationError(
                        f'This resource is already booked from '
                        f'{overlapping_booking.start_time.strftime("%Y-%m-%d %H:%M")} '
                        f'to {overlapping_booking.end_time.strftime("%Y-%m-%d %H:%M")}. '
                        f'Please choose a different time slot.'
                    )
        
        return cleaned_data
    
    def save(self, commit=True):
        booking = super().save(commit=False)
        if self.user:
            booking.user = self.user
        booking.status = 'Pending'
        if commit:
            booking.save()
        return booking


class ResourceFilterForm(forms.Form):
    """Form for filtering resources in the catalog."""
    
    category = forms.ChoiceField(
        choices=[('', 'All Categories')] + Resource.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search resources...',
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        })
    )
