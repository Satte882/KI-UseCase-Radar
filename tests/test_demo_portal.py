from django.urls import reverse

from ki_radar.accounts.views import RadarLoginView


def test_demo_portal_requires_authentication(client):
    response = client.get(reverse("demo-portal"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("accounts:login"))


def test_login_view_uses_demo_portal_as_default_target():
    assert RadarLoginView.next_page == "demo-portal"


def test_authenticated_user_sees_three_demo_entries(client, reader):
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


def test_existing_dashboard_url_is_preserved(client, reader):
    client.force_login(reader)

    assert reverse("reporting:dashboard") == "/"
    assert client.get(reverse("reporting:dashboard")).status_code == 200


def test_case_routes_are_protected_and_procurement_remains_placeholder(client, reader):
    for route_name in ("case-procurement", "case-sales-conversation"):
        anonymous_response = client.get(reverse(route_name))
        assert anonymous_response.status_code == 302
        assert anonymous_response.url.startswith(reverse("accounts:login"))

    client.force_login(reader)
    response = client.get(reverse("case-procurement"))

    assert response.status_code == 200
    assert "In Vorbereitung" in response.content.decode()


def test_sales_conversation_case_is_four_slide_web_presentation(client, reader):
    client.force_login(reader)

    response = client.get(reverse("case-sales-conversation"))
    body = response.content.decode()

    assert response.status_code == 200
    assert "In Vorbereitung" not in body
    for slide_number in range(1, 5):
        assert f'id="sci-slide-{slide_number}"' in body

    assert "Welche Merkmale eines Beratungsgesprächs erklären" in body
    assert "Der Case steht und fällt mit der Datenbasis." in body
    assert "Schlanker Pilot statt KI-Plattform." in body
    assert "Investieren erst nach drei Belegen." in body
    assert "Gate 1 negativ?" in body
    assert "2-wöchiger Data-&-Legal-Feasibility-Check" in body
    assert "6%" not in body
    assert "14%" not in body


def test_sales_conversation_case_uses_information_visualizations_not_card_grids(client, reader):
    client.force_login(reader)

    body = client.get(reverse("case-sales-conversation")).content.decode()

    assert 'class="sci-process-line"' in body
    assert 'class="sci-data-map"' in body
    assert 'class="sci-pipeline"' in body
    assert 'class="sci-gate-line"' in body
    assert "sci-flow-node" not in body
    assert "sci-panel" not in body


def test_authenticated_shell_exposes_small_home_control(client, reader):
    client.force_login(reader)

    response = client.get(reverse("reporting:dashboard"))
    body = response.content.decode()

    assert f'href="{reverse("demo-portal")}"' in body
    assert 'aria-label="Zur Startseite"' in body
    assert "⌂" in body
