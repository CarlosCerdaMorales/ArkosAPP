from django.shortcuts import render

from .models import Worker


def worker_list_view(request):
    workers = Worker.objects.all()
    return render(request, "workers/list.html", {"workers": workers})
