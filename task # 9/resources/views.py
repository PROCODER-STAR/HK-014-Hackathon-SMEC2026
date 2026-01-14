from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django import forms
from .models import Resource, Booking, Notification
from .forms import BookingForm, ResourceFilterForm


def is_admin(user):
    """Check if user is admin (you can customize this logic)."""
    return user.is_staff or user.is_superuser


@login_required
def resource_catalog(request):
    """Display searchable catalog of resources."""
    form = ResourceFilterForm(request.GET)
    resources = Resource.objects.all()
    
    if form.is_valid():
        category = form.cleaned_data.get('category')
        search = form.cleaned_data.get('search')
        
        if category:
            resources = resources.filter(category=category)
        
        if search:
            resources = resources.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
    
    context = {
        'resources': resources,
        'form': form,
    }
    return render(request, 'resources/catalog.html', context)


@login_required
def resource_detail(request, pk):
    """Display resource details and booking form."""
    resource = get_object_or_404(Resource, pk=pk)
    
    # Get upcoming approved bookings for this resource
    upcoming_bookings = Booking.objects.filter(
        resource=resource,
        status='Approved',
        start_time__gte=timezone.now()
    ).order_by('start_time')[:10]
    
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                booking = form.save()
                # Create notification
                Notification.objects.create(
                    user=request.user,
                    booking=booking,
                    message=f'Your booking request for {resource.name} has been submitted and is pending approval.'
                )
                messages.success(
                    request,
                    f'Booking request submitted successfully! Your request is pending approval.'
                )
                return redirect('booking_detail', pk=booking.pk)
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
    else:
        form = BookingForm(user=request.user)
        form.fields['resource'].initial = resource
        form.fields['resource'].widget = forms.HiddenInput()
    
    context = {
        'resource': resource,
        'form': form,
        'upcoming_bookings': upcoming_bookings,
    }
    return render(request, 'resources/resource_detail.html', context)


@login_required
def create_booking(request):
    """Create a new booking."""
    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                booking = form.save()
                # Create notification
                Notification.objects.create(
                    user=request.user,
                    booking=booking,
                    message=f'Your booking request for {booking.resource.name} has been submitted and is pending approval.'
                )
                messages.success(
                    request,
                    f'Booking request submitted successfully! Your request is pending approval.'
                )
                return redirect('booking_detail', pk=booking.pk)
            except Exception as e:
                messages.error(request, f'Error creating booking: {str(e)}')
    else:
        form = BookingForm(user=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'resources/create_booking.html', context)


@login_required
def booking_detail(request, pk):
    """Display booking details."""
    booking = get_object_or_404(Booking, pk=pk)
    
    # Ensure user can only view their own bookings (unless admin)
    if not is_admin(request.user) and booking.user != request.user:
        messages.error(request, 'You do not have permission to view this booking.')
        return redirect('my_bookings')
    
    context = {
        'booking': booking,
    }
    return render(request, 'resources/booking_detail.html', context)


@login_required
def my_bookings(request):
    """Display user's bookings."""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'bookings': bookings,
    }
    return render(request, 'resources/my_bookings.html', context)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard for managing bookings."""
    pending_bookings = Booking.objects.filter(status='Pending').order_by('created_at')
    recent_bookings = Booking.objects.all().order_by('-created_at')[:20]
    
    context = {
        'pending_bookings': pending_bookings,
        'recent_bookings': recent_bookings,
    }
    return render(request, 'resources/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def approve_booking(request, pk):
    """Approve a booking."""
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.status != 'Pending':
        messages.error(request, 'Only pending bookings can be approved.')
        return redirect('admin_dashboard')
    
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
        
        messages.success(request, 'Booking approved successfully!')
    except Exception as e:
        messages.error(request, f'Error approving booking: {str(e)}')
    
    return redirect('admin_dashboard')


@login_required
@user_passes_test(is_admin)
def reject_booking(request, pk):
    """Reject a booking."""
    booking = get_object_or_404(Booking, pk=pk)
    
    if booking.status != 'Pending':
        messages.error(request, 'Only pending bookings can be rejected.')
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        booking.status = 'Rejected'
        booking.rejection_reason = reason
        booking.save()
        
        # Create notification
        Notification.objects.create(
            user=booking.user,
            booking=booking,
            message=f'Your booking for {booking.resource.name} has been rejected. Reason: {reason if reason else "No reason provided."}'
        )
        
        messages.success(request, 'Booking rejected.')
        return redirect('admin_dashboard')
    
    context = {
        'booking': booking,
    }
    return render(request, 'resources/reject_booking.html', context)


@login_required
def notifications(request):
    """Display user notifications."""
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications_list.filter(is_read=False).count()
    
    # Mark as read when viewing
    if request.method == 'POST':
        notification_id = request.POST.get('notification_id')
        if notification_id:
            notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return redirect('notifications')
    
    context = {
        'notifications': notifications_list,
        'unread_count': unread_count,
    }
    return render(request, 'resources/notifications.html', context)
