import pytest
from django.test.client import Client

@pytest.fixture(autouse=True)
def _media_tmp(tmp_path, settings):
    media_dir = tmp_path / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    settings.MEDIA_ROOT = str(media_dir)

@pytest.fixture
def client():
    return Client()
