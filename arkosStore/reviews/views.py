from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReviewForm
from .models import Review
from appointments.models import Appointment, StatusChoices

@login_required
def create_review_view(request, appointment_id):
    # Obtener la cita y verificar permisos
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        user=request.user
    )
    
    # Verificar que la cita esté completada
    if appointment.status != StatusChoices.COMPLETED:
        messages.error(request, 'Solo puedes valorar citas completadas.')
        return redirect('appointment_history')
    
    # Verificar que no tenga ya una review
    if hasattr(appointment, 'review'):
        messages.warning(request, 'Ya has valorado esta cita.')
        return redirect('appointment_history')
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.appointment = appointment
            review.save()
            messages.success(request, '¡Gracias por tu valoración!')
            return redirect('appointment_history')
    else:
        form = ReviewForm()
    
    context = {
        'form': form,
        'appointment': appointment
    }
    return render(request, 'reviews/create.html', context)

@login_required
def my_reviews_view(request):
    reviews = Review.objects.filter(
        appointment__user=request.user
    ).order_by('-date')
    
    return render(request, 'reviews/my_reviews.html', {'reviews': reviews})