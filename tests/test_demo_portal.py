from django.urls import reverse

from ki_radar.accounts.views import RadarLoginView


def test_demo_portal_requires_authentication(client):
    response = client.get(reverse("demo-portal"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_login_view_uses_demo_portal_as_default_target():
    assert RadarLoginView.next_page == "demo-portal"


def test_authenticated_user_sees_three_equal_presentation_entries(client, reader):
    client.force_login(reader)

    response = client.get(reverse("demo-portal"))
    body = response.content.decode()

    assert response.status_code == 200
    assert "Projektbeispiel: Angebotsvergleich im Einkauf" in body
    assert "Use Case: Sales Conversation Intelligence" in body
    assert "Anwendung: KI-Use-Case-Radar" in body
    assert f'href="{reverse("case-procurement")}"' in body
    assert f'href="{reverse("case-sales-conversation")}"' in body
    assert f'href="{reverse("reporting:dashboard")}"' in body
    assert body.count('class="presentation-card"') == 3
    assert "presentation-rsd-brand" in body
    assert "img/rsd-logo.svg" in body
    assert "Vorbereitet für RSD" in body
    assert "app-sidebar" not in body
    assert "Arbeitsvorrat" not in body


def test_existing_dashboard_url_is_preserved(client, reader):
    client.force_login(reader)

    assert reverse("reporting:dashboard") == "/"
    assert client.get(reverse("reporting:dashboard")).status_code == 200


def test_case_routes_are_protected_and_use_presentation_shell(client, reader):
    for route_name in ("case-procurement", "case-sales-conversation"):
        anonymous_response = client.get(reverse(route_name))
        assert anonymous_response.status_code == 302
        assert anonymous_response.url.startswith(reverse("accounts:login"))

    client.force_login(reader)
    for route_name in ("case-procurement", "case-sales-conversation"):
        response = client.get(reverse(route_name))
        body = response.content.decode()
        assert response.status_code == 200
        assert "In Vorbereitung" in body
        assert "presentation-rsd-brand" in body
        assert "app-sidebar" not in body


def test_authenticated_app_shell_keeps_return_link_to_demo_portal(client, reader):
    client.force_login(reader)

    response = client.get(reverse("reporting:dashboard"))
    body = response.content.decode()

    assert f'href="{reverse("demo-portal")}"' in body
    assert 'aria-label="Zur Startseite"' in body
