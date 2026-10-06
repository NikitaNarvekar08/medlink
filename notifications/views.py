from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    items = Notification.objects.filter(user=request.user).order_by("-created_at")[:50]
    return render(request, "notifications/list.html", {"items": items})


@login_required
@require_POST
def open_notification(request, pk):
    try:
        note = get_object_or_404(Notification, pk=pk, user=request.user)
    except ValidationError:
        raise Http404
    if not note.is_read:
        note.is_read = True
        note.save(update_fields=["is_read"])
    if note.link.startswith("/"):
        return redirect(note.link)
    return redirect("notifications:list")


@login_required
@require_POST
def mark_all_read(request):
    for note in Notification.objects.filter(user=request.user, is_read=False):
        note.is_read = True
        note.save(update_fields=["is_read"])
    return redirect("notifications:list")