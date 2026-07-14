from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import WorkItemForm
from .models import WorkItem


@login_required
def item_list(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = WorkItemForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("workitems:list")
        return render(
            request,
            "workitems/list.html",
            {"items": WorkItem.objects.all(), "form": form},
            status=400,
        )
    form = WorkItemForm()
    return render(
        request,
        "workitems/list.html",
        {"items": WorkItem.objects.all(), "form": form},
    )


@login_required
def complete_item(request: HttpRequest, pk: int) -> HttpResponse:
    if request.method != "POST":
        return HttpResponse(status=405)
    item = get_object_or_404(WorkItem, pk=pk)
    item.completed = True
    item.save()
    return redirect("workitems:list")
