"""Tests that the production static manifest contains the compiled Sass output.

These tests are skipped when ``collected_static/`` has not been built yet
(normal for local development).  In CI the "Build production static files"
step runs *before* pytest so the manifest is always present there.
"""

import json
import os

import pytest
from django.test import Client, override_settings

_MANIFEST = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "collected_static",
    "staticfiles.json",
)

_MANIFEST_BUILT = os.path.isfile(_MANIFEST)


@pytest.mark.skipif(not _MANIFEST_BUILT, reason="collected_static not yet built")
def test_styles_css_in_manifest() -> None:
    """styles.css must appear as a key in the production staticfiles manifest.

    If this fails it means ``compilescss`` did not run before
    ``collectstatic``, so the Sass-generated CSS was never collected and
    ManifestStaticFilesStorage cannot resolve the hashed URL.
    """
    with open(_MANIFEST) as fh:
        manifest = json.load(fh)
    assert "styles.css" in manifest["paths"], (
        "styles.css is absent from collected_static/staticfiles.json; ensure `compilescss` runs before `collectstatic`."
    )


@pytest.mark.skipif(not _MANIFEST_BUILT, reason="collected_static not yet built")
def test_bio_page_renders_with_manifest_storage() -> None:
    """Bio page must not raise a ManifestStaticFilesStorage lookup error.

    The template uses ``{% sass_src 'styles.scss' %}``, which resolves
    through the staticfiles storage.  Under production's
    CompressedManifestStaticFilesStorage this raises ``ValueError`` when
    styles.css is missing from the manifest.
    """
    with override_settings(
        PRODUCTION=True,
        DEBUG=False,
        SECRET_KEY="ci-static-test-secret-key-long-enough-for-django",
        SECURE_SSL_REDIRECT=False,
        ALLOWED_HOSTS=["testserver", "localhost"],
        STORAGES={
            "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
            "staticfiles": {"BACKEND": ("whitenoise.storage.CompressedManifestStaticFilesStorage")},
        },
    ):
        response = Client().get("/who-is-ben-welsh/")
    assert response.status_code == 200
    content = response.content.decode()
    assert "/static/img/ben-blue-800." in content
    assert "/static/img/ben-blue-800.webp" not in content
    assert "/static/img/ben-blue-800.jpg" not in content
