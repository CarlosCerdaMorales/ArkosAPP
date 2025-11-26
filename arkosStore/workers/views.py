from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from accounts.models import User
from .models import Worker
from .forms import WorkerForm

def worker_list_view(request):
    workers = Worker.objects.all()
    return render(request, "workers/list.html", {"workers": workers})

def is_admin(user):
    return user.is_authenticated and user.role == User.Role.ADMIN

@user_passes_test(is_admin)
def admin_create_worker(request):
    if request.method == "POST":
        form = WorkerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("custom_admin")
    else:
        form = WorkerForm()
    return render(request, "workers/admin_create_worker.html", {"form": form})
