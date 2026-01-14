from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone


class Resource(models.Model):
    """Model representing a campus resource (Lab, Hall, or Equipment)."""
    
    CATEGORY_CHOICES = [
        ('Lab', 'Lab'),
        ('Hall', 'Seminar Hall'),
        ('Equipment', 'Equipment'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    capacity = models.PositiveIntegerField(help_text="Maximum number of people or items")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    def is_available(self, start_time, end_time, exclude_booking=None):
        """
        Check if resource is available for the given time slot.
        Excludes the booking specified (useful for updates).
        """
        overlapping = Booking.objects.filter(
            resource=self,
            status='Approved',
            start_time__lt=end_time,
            end_time__gt=start_time
        )
        
        if exclude_booking:
            overlapping = overlapping.exclude(pk=exclude_booking.pk)
        
        return not overlapping.exists()


class Booking(models.Model):
    """Model representing a booking request for a resource."""
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='bookings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection (if applicable)")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking'
        verbose_name_plural = 'Bookings'
    
    def __str__(self):
        return f"{self.user.username} - {self.resource.name} ({self.start_time.date()})"
    
    def clean(self):
        """Validate booking to prevent overlapping bookings."""
        # Ensure end_time is after start_time
        if self.end_time <= self.start_time:
            raise ValidationError({
                'end_time': 'End time must be after start time.'
            })
        
        # Ensure booking is not in the past
        if self.start_time < timezone.now():
            raise ValidationError({
                'start_time': 'Cannot book resources in the past.'
            })
        
        # Check for overlapping bookings only if status is Approved or will be Approved
        # For new bookings, we check if the resource would be available
        if self.status == 'Approved' or self.pk is None:
            # Get existing approved bookings that overlap
            overlapping = Booking.objects.filter(
                resource=self.resource,
                status='Approved',
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            
            # Exclude self if updating
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            
            if overlapping.exists():
                overlapping_booking = overlapping.first()
                raise ValidationError(
                    f'This resource is already booked from {overlapping_booking.start_time} '
                    f'to {overlapping_booking.end_time}. Please choose a different time slot.'
                )
    
    def save(self, *args, **kwargs):
        """Override save to call clean validation."""
        self.full_clean()
        super().save(*args, **kwargs)


class Notification(models.Model):
    """Simple notification model for booking status updates."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"Notification for {self.user.username} - {self.message[:50]}"
