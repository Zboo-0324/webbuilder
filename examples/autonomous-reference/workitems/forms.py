from django import forms

from .models import WorkItem


class WorkItemForm(forms.ModelForm):
    title = forms.CharField(max_length=200, required=False)

    class Meta:
        model = WorkItem
        fields = ("title",)

    def clean_title(self) -> str:
        value = self.cleaned_data.get("title", "").strip()
        if not value:
            raise forms.ValidationError("Title is required")
        return value
