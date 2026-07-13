from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import WorkItem


class WorkItemFlowTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user("reviewer", password="review-pass")

    def test_anonymous_user_is_redirected_to_login(self) -> None:
        response = self.client.get(reverse("workitems:list"))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('workitems:list')}")

    def test_authenticated_user_can_create_and_complete_an_item(self) -> None:
        self.client.force_login(self.user)
        created = self.client.post(reverse("workitems:list"), {"title": "Review case 42"})
        item = WorkItem.objects.get()
        self.assertRedirects(created, reverse("workitems:list"))
        completed = self.client.post(reverse("workitems:complete", args=[item.pk]))
        self.assertRedirects(completed, reverse("workitems:list"))
        item.refresh_from_db()
        self.assertTrue(item.completed)

    def test_empty_title_is_visible_validation_error(self) -> None:
        self.client.force_login(self.user)
        response = self.client.post(reverse("workitems:list"), {"title": ""})
        self.assertContains(response, "Title is required", status_code=400)

    def test_authenticated_list_page_offers_post_logout_control(self) -> None:
        """The list page must present logout as a POST form, not a GET link.

        Django 5.2 LogoutView only accepts POST (and OPTIONS); rendering
        logout as a plain <a> link produces HTTP 405 Method Not Allowed.
        """
        self.client.force_login(self.user)
        response = self.client.get(reverse("workitems:list"))
        logout_url = reverse("logout")
        # The logout URL must appear in a <form action="…">, not an <a href="…">.
        self.assertContains(
            response,
            f'action="{logout_url}"',
            msg_prefix="Expected a <form> targeting the logout URL",
        )
        self.assertNotContains(
            response,
            f'href="{logout_url}"',
            msg_prefix="Logout must not be a GET link",
        )


class SeedReviewerPasswordTests(TestCase):
    """Regression: seed_reference must guarantee the reviewer password.

    If the reviewer user already exists with a stale password, re-running
    seed_reference must still leave the correct password in place.
    """

    def test_seed_overwrites_pre_existing_reviewer_password(self) -> None:
        User = get_user_model()
        # Create the reviewer with a deliberately wrong password.
        User.objects.create_user("reviewer", password="stale-password")

        call_command("seed_reference")

        reviewers = User.objects.filter(username="reviewer")
        self.assertEqual(reviewers.count(), 1, "Expected exactly one reviewer user")
        reviewer = reviewers.get()
        self.assertTrue(
            reviewer.check_password("review-pass"),
            "seed_reference must ensure the reviewer password is 'review-pass', "
            "even when the user already existed with a different password",
        )
