import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_user_pagination():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/users?page=2&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert len(data["data"]) <= 10

@pytest.mark.asyncio
async def test_role_assignment():
    # 測試角色分配功能... 

@pytest.mark.asyncio
async def test_user_pagination_edge_cases():
    cases = [
        ("page=0", 422),
        ("per_page=1000", 422),
        ("page=3&per_page=5", 200)
    ]
    
    for qs, expected in cases:
        response = await client.get(f"/users?{qs}")
        assert response.status_code == expected 