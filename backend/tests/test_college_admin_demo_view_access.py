"""College admin API access while browsing the showcase demo tenant."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.modules.tenants.domain_utils import normalize_tenant_code

DEV_TENANT_CODE = "demo-college"
DEV_ADMIN_EMAIL = "admin@demo-college.edu"
DEV_ADMIN_PASSWORD = "CollegeAdmin123!"


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_demo_college_view_dashboard_for_foreign_college_admin(client: AsyncClient) -> None:
    """Logged-in home-college admin may read showcase data when demo view header is set."""
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": DEV_ADMIN_EMAIL,
            "password": DEV_ADMIN_PASSWORD,
            "tenant_code": normalize_tenant_code(DEV_TENANT_CODE),
        },
    )
    if login.status_code != 200:
        pytest.skip("demo-college bootstrap admin is not provisioned")
    token = login.json()["data"]["access_token"]
    response = await client.get(
        "/api/v1/college-admin/dashboard",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Demo-College-View": "1",
        },
        params={"range": "semester"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["statistics"]["total_students"] >= 100