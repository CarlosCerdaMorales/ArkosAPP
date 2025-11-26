from django import forms
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.models import User
from workers.models import Worker
from .models import Availability


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ["day_of_week", "start_time", "end_time"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
        }


def is_admin(user):
    return user.is_authenticated and user.role == User.Role.ADMIN


@user_passes_test(is_admin)
def admin_manage_availability(request):
    workers = Worker.objects.all().order_by("name")
    selected_worker = None
    selected_worker_id = request.GET.get("worker")

    if selected_worker_id:
        try:
            selected_worker = workers.get(id=selected_worker_id)
        except Worker.DoesNotExist:
            selected_worker = None
    elif workers.exists():
        selected_worker = workers.first()

    availabilities = []
    if selected_worker:
        availabilities = Availability.objects.filter(worker=selected_worker).order_by(
            "day_of_week", "start_time"
        )

    if request.method == "POST":
        if "delete_id" in request.POST:
            delete_id = request.POST.get("delete_id")
            Availability.objects.filter(id=delete_id).delete()
            url = reverse("admin_manage_availability")
            if selected_worker:
                url = f"{url}?worker={selected_worker.id}"
            return redirect(url)

        form = AvailabilityForm(request.POST)
        if selected_worker:
            form.instance.worker = selected_worker
        if form.is_valid():
            form.save()
            url = reverse("admin_manage_availability")
            if selected_worker:
                url = f"{url}?worker={selected_worker.id}"
            return redirect(url)
    else:
        form = AvailabilityForm()

    context = {
        "workers": workers,
        "selected_worker": selected_worker,
        "availabilities": availabilities,
        "form": form,
    }
    return render(request, "appointments/admin_manage_availability.html", context)
