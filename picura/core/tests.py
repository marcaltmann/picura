import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse


@pytest.fixture
def user(db):
    return get_user_model().objects.create_user(username='alice', password='pw')


@pytest.mark.django_db
def test_header_shows_sign_in_link_when_anonymous(client):
    response = client.get(reverse('welcome'))
    assert reverse('account_login').encode() in response.content


@pytest.mark.django_db
def test_header_shows_sign_out_when_authenticated(client, user):
    client.force_login(user)
    response = client.get(reverse('welcome'))
    assert reverse('account_logout').encode() in response.content
    assert b'alice' in response.content


@pytest.mark.django_db
def test_login_page_uses_project_layout(client):
    response = client.get(reverse('account_login'))
    assert response.status_code == 200
    # The allauth layout override pulls in the project header.
    assert b'class="header"' in response.content


@pytest.mark.django_db
def test_signup_page_renders(client):
    response = client.get(reverse('account_signup'))
    assert response.status_code == 200
    assert b'class="header"' in response.content
