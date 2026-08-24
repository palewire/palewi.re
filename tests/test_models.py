"""Tests for models and managers."""

import pytest
from django.contrib.auth.models import User

from coltrane.models import Post


@pytest.fixture
def author(db):
    return User.objects.create_user(username="testuser", password="password")


@pytest.mark.django_db
def test_live_post_manager_returns_live_only(author):
    post = Post.objects.create(
        title="Live post",
        slug="live-post",
        body_markup="body",
        status=Post.LIVE_STATUS,
        pub_date="2024-01-01 00:00:00",
        author=author,
    )
    Post.objects.create(
        title="Draft post",
        slug="draft-post",
        body_markup="body",
        status=Post.DRAFT_STATUS,
        pub_date="2024-01-01 00:00:00",
        author=author,
    )
    live = Post.live.all()
    assert post in live
    for candidate in live:
        assert candidate.status == Post.LIVE_STATUS
