from django.urls import path

from . import views

app_name = "workitems"

urlpatterns = [
    path("", views.item_list, name="list"),
    path("complete/<int:pk>/", views.complete_item, name="complete"),
]
