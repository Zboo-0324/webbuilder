from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from workitems.models import WorkItem


class Command(BaseCommand):
    help = "Seed the reference application with deterministic data."

    def handle(self, *args, **options) -> None:
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="reviewer",
            defaults={"email": "reviewer@example.com"},
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created user 'reviewer'."))
        else:
            self.stdout.write("User 'reviewer' already exists.")
        user.set_password("review-pass")
        user.save()

        item, created = WorkItem.objects.get_or_create(
            title="Review the autonomous delivery evidence",
            defaults={"completed": False},
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS("Created work item 'Review the autonomous delivery evidence'.")
            )
        else:
            self.stdout.write("Work item 'Review the autonomous delivery evidence' already exists.")
