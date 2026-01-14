from django.contrib import admin
from django.utils.html import format_html
from .models import Resource, Booking, Notification


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'capacity', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'description', 'capacity')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['user', 'resource', 'resource_capacity', 'start_time', 'end_time', 'status', 'created_at', 'status_colored']
    list_filter = ['status', 'resource__category', 'start_time', 'created_at']
    search_fields = ['user__username', 'resource__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_time'
    
    fieldsets = (
        ('Booking Details', {
            'fields': ('user', 'resource', 'start_time', 'end_time', 'status')
        }),
        ('Additional Information', {
            'fields': ('rejection_reason',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def resource_capacity(self, obj):
        """Display resource capacity in the list view."""
        return obj.resource.capacity
    resource_capacity.short_description = 'Capacity'
    resource_capacity.admin_order_field = 'resource__capacity'
    
    def status_colored(self, obj):
        """Display status with color coding."""
        colors = {
            'Pending': 'orange',
            'Approved': 'green',
            'Rejected': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status
        )
    status_colored.short_description = 'Status'
    
    actions = ['approve_bookings', 'reject_bookings']
    
    def approve_bookings(self, request, queryset):
        """Bulk approve selected bookings."""
        count = 0
        for booking in queryset:
            if booking.status == 'Pending':
                # Check for overlaps before approving
                try:
                    booking.status = 'Approved'
                    booking.full_clean()  # This will validate overlaps
                    booking.save()
                    # Create notification
                    Notification.objects.create(
                        user=booking.user,
                        booking=booking,
                        message=f'Your booking for {booking.resource.name} has been approved!'
                    )
                    count += 1
                except Exception as e:
                    self.message_user(
                        request,
                        f'Could not approve booking {booking.id}: {str(e)}',
                        level='ERROR'
                    )
        self.message_user(request, f'{count} booking(s) approved successfully.')
    approve_bookings.short_description = 'Approve selected bookings'
    
    def reject_bookings(self, request, queryset):
        """Bulk reject selected bookings."""
        count = queryset.update(status='Rejected')
        # Create notifications for rejected bookings
        for booking in queryset.filter(status='Rejected'):
            Notification.objects.create(
                user=booking.user,
                booking=booking,
                message=f'Your booking for {booking.resource.name} has been rejected.'
            )
        self.message_user(request, f'{count} booking(s) rejected.')
    reject_bookings.short_description = 'Reject selected bookings'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'booking', 'message_short', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['user__username', 'message']
    readonly_fields = ['created_at']
    
    def message_short(self, obj):
        """Display shortened message."""
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = 'Message'
