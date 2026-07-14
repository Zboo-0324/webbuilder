from django.db import models


class WorkItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("completed", "-created_at")

    def __str__(self) -> str:
        return self.title
