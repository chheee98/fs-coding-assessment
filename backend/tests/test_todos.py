"""Tests for Todo CRUD endpoints."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from faker import Faker
from httpx import AsyncClient

# ============================================================
# Required Tests by this Assessment
# ============================================================


class TestRequiredByAssessment:

    @pytest.mark.asyncio
    async def test_create_todo_success(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        todo_data = {
            "title": fake.sentence(nb_words=4),
            "description": fake.paragraph(),
            "priority": fake.random_element(["LOW", "MEDIUM", "HIGH"]),
        }

        # Act
        response = await client.post(
            "/api/v1/todos", json=todo_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["description"] == todo_data["description"]
        assert data["priority"] == todo_data["priority"]
        assert data["status"] == "NOT_STARTED"
        assert data["due_date"] is None
        assert "id" in data
        assert data["user_id"] == auth_user["user"]["id"]
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_all_todos(
        self,
        client: AsyncClient,
        auth_user: dict,
        second_auth_user: dict,
        fake: Faker,
    ):
        # Arrange
        todo1 = {
            "title": fake.sentence(nb_words=3),
            "description": fake.paragraph(),
            "priority": "LOW",
        }
        todo2 = {
            "title": fake.sentence(nb_words=3),
            "description": fake.paragraph(),
            "priority": "MEDIUM",
        }
        await client.post("/api/v1/todos", json=todo1, headers=auth_user["headers"])
        user1_id = auth_user["user"]["id"]

        await client.post(
            "/api/v1/todos", json=todo2, headers=second_auth_user["headers"]
        )

        # Act
        response = await client.get("/api/v1/todos", headers=auth_user["headers"])

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data

        items = data["items"]
        assert len(items) >= 2

        own_items = [i for i in items if i["user_id"] == user1_id]
        other_items = [i for i in items if i["user_id"] != user1_id]

        for item in own_items:
            assert item["description"] is not None

        for item in other_items:
            assert item["description"] is None


# ============================================================
# Todo CRUD Endpoints
# ============================================================


class TestCreateTodo:

    @pytest.mark.asyncio
    async def test_create_with_all_fields(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange — simulate a real frontend in GMT+7 sending local time
        local_tz = timezone(timedelta(hours=7))
        todo_data = {
            "title": fake.sentence(nb_words=4),
            "description": fake.paragraph(),
            "priority": fake.random_element(["LOW", "MEDIUM", "HIGH"]),
            "due_date": fake.future_datetime(tzinfo=local_tz).isoformat(),
        }
        sent_due_date = datetime.fromisoformat(todo_data["due_date"])

        # Act
        response = await client.post(
            "/api/v1/todos", json=todo_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["description"] == todo_data["description"]
        assert data["priority"] == todo_data["priority"]
        # Compare as datetime — same instant, different representation (+07:00 vs UTC)
        response_due_date = datetime.fromisoformat(data["due_date"])
        assert response_due_date == sent_due_date
        assert data["user_id"] == auth_user["user"]["id"]
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_with_minimal_fields(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange — only title is required
        todo_data = {"title": fake.sentence(nb_words=3)}

        # Act
        response = await client.post(
            "/api/v1/todos", json=todo_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == todo_data["title"]
        assert data["description"] == ""
        assert data["priority"] is None
        assert data["due_date"] is None

    @pytest.mark.asyncio
    async def test_create_without_auth(self, client: AsyncClient, fake: Faker):
        # Arrange
        todo_data = {"title": fake.sentence(nb_words=3)}

        # Act — no auth headers
        response = await client.post("/api/v1/todos", json=todo_data)

        # Assert
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_invalid_priority(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        todo_data = {"title": fake.sentence(nb_words=3), "priority": "INVALID"}

        # Act
        response = await client.post(
            "/api/v1/todos",
            json=todo_data,
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        field_names = [err["loc"][-1] for err in errors]
        assert "priority" in field_names

    @pytest.mark.asyncio
    async def test_create_with_empty_body(self, client: AsyncClient, auth_user: dict):
        # Arrange
        todo_data = {}

        # Act
        response = await client.post(
            "/api/v1/todos", json=todo_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        for err in errors:
            assert err["loc"] == ["body", "title"]
            assert err["type"] == "missing"

    @pytest.mark.asyncio
    async def test_create_with_empty_title(self, client: AsyncClient, auth_user: dict):
        # Arrange
        todo_data = {"title": ""}

        # Act
        response = await client.post(
            "/api/v1/todos", json=todo_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        field_names = [err["loc"][-1] for err in errors]
        assert "title" in field_names

    @pytest.mark.asyncio
    async def test_create_with_past_due_date(
        self, client: AsyncClient, auth_user: dict
    ):
        # Arrange
        todo_data = {"title": "Late Todo", "due_date": "2000-01-01T00:00:00"}

        # Act
        response = await client.post(
            "/api/v1/todos", json=todo_data, headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 422
        errors = response.json()["detail"]
        field_names = [err["loc"][-1] for err in errors]
        assert "due_date" in field_names

    @pytest.mark.asyncio
    async def test_create_with_timezone_aware_due_date(
        self, client: AsyncClient, auth_user: dict
    ):
        # Arrange — due_date with Z (UTC timezone-aware)
        todo_data = {"title": "Timezone test", "due_date": "2099-01-01T00:00:00Z"}

        # Act
        response = await client.post(
            "/api/v1/todos", json=todo_data, headers=auth_user["headers"]
        )

        # Assert — should succeed, not 500
        assert response.status_code == 201
        assert response.json()["due_date"] is not None


class TestGetTodos:

    @pytest.mark.asyncio
    async def test_get_empty_list(self, client: AsyncClient, auth_user: dict):
        # Act — fresh user, no todos created
        response = await client.get("/api/v1/todos", headers=auth_user["headers"])

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "items" in data and len(data["items"]) == 0
        assert "total" in data

    @pytest.mark.asyncio
    async def test_get_with_pagination(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange — create 3 todos, request page_size=2
        for _ in range(3):
            await client.post(
                "/api/v1/todos",
                json={"title": fake.sentence(nb_words=3)},
                headers=auth_user["headers"],
            )

        # Act
        response = await client.get(
            "/api/v1/todos?page=1&page_size=2", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    @pytest.mark.asyncio
    async def test_pagination_order_is_deterministic(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange — create 3 todos sequentially
        created_ids = []
        for _ in range(3):
            resp = await client.post(
                "/api/v1/todos",
                json={"title": fake.sentence(nb_words=3)},
                headers=auth_user["headers"],
            )
            created_ids.append(resp.json()["id"])

        # Act — fetch twice, same page
        response1 = await client.get(
            "/api/v1/todos?page=1&page_size=10", headers=auth_user["headers"]
        )
        response2 = await client.get(
            "/api/v1/todos?page=1&page_size=10", headers=auth_user["headers"]
        )

        # Assert — same order both times, newest first
        ids1 = [item["id"] for item in response1.json()["items"]]
        ids2 = [item["id"] for item in response2.json()["items"]]
        assert ids1 == ids2

        # Verify newest todo is first (last created = first in list)
        assert ids1[0] == created_ids[-1]

    @pytest.mark.asyncio
    async def test_filter_by_priority(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3), "priority": "HIGH"},
            headers=auth_user["headers"],
        )
        await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3), "priority": "LOW"},
            headers=auth_user["headers"],
        )

        # Act
        response = await client.get(
            "/api/v1/todos?priority=HIGH", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["priority"] == "HIGH"

    @pytest.mark.asyncio
    async def test_filter_by_completed(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange — create and complete a todo
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]
        await client.patch(
            f"/api/v1/todos/{todo_id}/complete", headers=auth_user["headers"]
        )

        # Act
        response = await client.get(
            "/api/v1/todos?completed=true", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        items = response.json()["items"]
        for item in items:
            assert item["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_search_by_exact_word(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        unique_word = fake.unique.word()
        await client.post(
            "/api/v1/todos",
            json={"title": f"Search {unique_word} Todo"},
            headers=auth_user["headers"],
        )

        # Act
        response = await client.get(
            f"/api/v1/todos?search={unique_word}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 1
        assert any(unique_word in item["title"] for item in items)

    @pytest.mark.asyncio
    async def test_search_by_partial_word(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        unique_word = fake.unique.word()
        partial_search = unique_word[1:-1]
        await client.post(
            "/api/v1/todos",
            json={"title": f"Search {unique_word} Todo"},
            headers=auth_user["headers"],
        )

        # Act — search with partial word (ILIKE)
        response = await client.get(
            f"/api/v1/todos?search={partial_search}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) >= 1
        assert any(partial_search.lower() in item["title"].lower() for item in items)

    @pytest.mark.asyncio
    async def test_description_hidden_for_non_owner(
        self,
        client: AsyncClient,
        auth_user: dict,
        second_auth_user: dict,
        fake: Faker,
    ):
        # Arrange — user1 creates a todo with description
        await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3), "description": fake.paragraph()},
            headers=auth_user["headers"],
        )

        # Act — user2 lists todos
        response = await client.get(
            "/api/v1/todos", headers=second_auth_user["headers"]
        )

        # Assert — user1's description hidden from user2
        assert response.status_code == 200
        items = response.json()["items"]
        other_items = [i for i in items if i["user_id"] == auth_user["user"]["id"]]
        for item in other_items:
            assert item["description"] is None

    @pytest.mark.asyncio
    async def test_get_without_auth(self, client: AsyncClient):
        # Act
        response = await client.get("/api/v1/todos")

        # Assert
        assert response.status_code == 401


class TestGetTodo:

    @pytest.mark.asyncio
    async def test_get_own_todo(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3), "description": fake.paragraph()},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act
        response = await client.get(
            f"/api/v1/todos/{todo_id}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["user_id"] == auth_user["user"]["id"]

    @pytest.mark.asyncio
    async def test_get_other_user_todo(
        self,
        client: AsyncClient,
        auth_user: dict,
        second_auth_user: dict,
        fake: Faker,
    ):
        # Arrange — user1 creates a todo
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — user2 tries to access it
        response = await client.get(
            f"/api/v1/todos/{todo_id}", headers=second_auth_user["headers"]
        )

        # Assert
        assert response.status_code == 403
        assert (response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)

    @pytest.mark.asyncio
    async def test_get_nonexistent_todo(self, client: AsyncClient, auth_user: dict):
        # Act
        response = await client.get(
            f"/api/v1/todos/{uuid.uuid4()}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 404
        assert (response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)


class TestUpdateTodo:

    @pytest.mark.asyncio
    async def test_update_title(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]
        new_title = fake.sentence(nb_words=4)

        # Act
        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"title": new_title},
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["title"] == new_title

    @pytest.mark.asyncio
    async def test_partial_update(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3), "priority": "LOW"},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — update only priority, title should stay
        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"priority": "HIGH"},
            headers=auth_user["headers"],
        )

        # Assert — only priority changed, everything else unchanged
        assert response.status_code == 200
        data = response.json()
        original = create_response.json()
        assert data["priority"] == "HIGH"
        assert data["title"] == original["title"]
        assert data["description"] == original["description"]
        assert data["due_date"] == original["due_date"]
        assert data["status"] == original["status"]
        assert data["user_id"] == original["user_id"]

    @pytest.mark.asyncio
    async def test_update_other_user_todo(
        self,
        client: AsyncClient,
        auth_user: dict,
        second_auth_user: dict,
        fake: Faker,
    ):
        # Arrange — user1 creates a todo
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — user2 tries to update it
        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"title": "Hacked"},
            headers=second_auth_user["headers"],
        )

        # Assert
        assert response.status_code == 403
        assert (response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)

    @pytest.mark.asyncio
    async def test_update_nonexistent_todo(self, client: AsyncClient, auth_user: dict):
        # Act
        response = await client.patch(
            f"/api/v1/todos/{uuid.uuid4()}",
            json={"title": "Nope"},
            headers=auth_user["headers"],
        )

        # Assert
        assert response.status_code == 404
        assert (response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)

    @pytest.mark.asyncio
    async def test_update_with_timezone_aware_due_date(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — update due_date with Z (UTC timezone-aware)
        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"due_date": "2099-01-01T00:00:00Z"},
            headers=auth_user["headers"],
        )

        # Assert — should succeed, not 500
        assert response.status_code == 200
        assert response.json()["due_date"] is not None

    @pytest.mark.asyncio
    async def test_update_null_title_rejected(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — send explicit null for non-nullable field
        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"title": None},
            headers=auth_user["headers"],
        )

        # Assert — 422, not 500
        assert response.status_code == 422
        errors = response.json()["detail"]
        field_names = [err["loc"][-1] for err in errors]
        assert "title" in field_names

    @pytest.mark.asyncio
    async def test_update_null_description_rejected(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3), "description": "Keep me"},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — send explicit null for non-nullable field
        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"description": None},
            headers=auth_user["headers"],
        )

        # Assert — 422, not 500
        assert response.status_code == 422
        errors = response.json()["detail"]
        field_names = [err["loc"][-1] for err in errors]
        assert "description" in field_names

    @pytest.mark.asyncio
    async def test_update_null_status_rejected(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — send explicit null for non-nullable field
        response = await client.patch(
            f"/api/v1/todos/{todo_id}",
            json={"status": None},
            headers=auth_user["headers"],
        )

        # Assert — 422, not 500
        assert response.status_code == 422
        errors = response.json()["detail"]
        field_names = [err["loc"][-1] for err in errors]
        assert "status" in field_names


class TestDeleteTodo:

    @pytest.mark.asyncio
    async def test_delete_own_todo(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act
        response = await client.delete(
            f"/api/v1/todos/{todo_id}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/v1/todos/{todo_id}", headers=auth_user["headers"]
        )
        assert get_response.status_code == 404
        assert (get_response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)

    @pytest.mark.asyncio
    async def test_delete_other_user_todo(
        self,
        client: AsyncClient,
        auth_user: dict,
        second_auth_user: dict,
        fake: Faker,
    ):
        # Arrange — user1 creates a todo
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — user2 tries to delete it
        response = await client.delete(
            f"/api/v1/todos/{todo_id}", headers=second_auth_user["headers"]
        )

        # Assert
        assert response.status_code == 403
        assert (response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_todo(self, client: AsyncClient, auth_user: dict):
        # Act
        response = await client.delete(
            f"/api/v1/todos/{uuid.uuid4()}", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 404
        assert (response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)


class TestToggleComplete:

    @pytest.mark.asyncio
    async def test_toggle_to_completed(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act
        response = await client.patch(
            f"/api/v1/todos/{todo_id}/complete", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"

        # Verify via GET
        get_response = await client.get(
            f"/api/v1/todos/{todo_id}", headers=auth_user["headers"]
        )
        assert get_response.json()["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_toggle_back_to_not_started(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange — create and complete
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]
        await client.patch(
            f"/api/v1/todos/{todo_id}/complete", headers=auth_user["headers"]
        )

        # Act — toggle again
        response = await client.patch(
            f"/api/v1/todos/{todo_id}/complete", headers=auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "NOT_STARTED"

        # Verify via GET
        get_response = await client.get(
            f"/api/v1/todos/{todo_id}", headers=auth_user["headers"]
        )
        assert get_response.json()["status"] == "NOT_STARTED"

    @pytest.mark.asyncio
    async def test_toggle_other_user_todo(
        self,
        client: AsyncClient,
        auth_user: dict,
        second_auth_user: dict,
        fake: Faker,
    ):
        # Arrange — user1 creates a todo
        create_response = await client.post(
            "/api/v1/todos",
            json={"title": fake.sentence(nb_words=3)},
            headers=auth_user["headers"],
        )
        todo_id = create_response.json()["id"]

        # Act — user2 tries to toggle it
        response = await client.patch(
            f"/api/v1/todos/{todo_id}/complete",
            headers=second_auth_user["headers"],
        )

        # Assert
        assert response.status_code == 403
        assert (response.json()).get(
            "detail"
        )  # detail must exists (not None / not empty)


# ============================================================
# Stats Endpoint
# ============================================================


class TestGetStats:
    """Tests are order-dependent — do NOT reorder. Later tests rely on DB state from earlier ones."""

    # --- Test data: {priority: (total, completed)} ---
    AUTH1_SETUP = {"LOW": (3, 2), "MEDIUM": (4, 1), "HIGH": (3, 1)}
    AUTH1_TOTAL = sum(t for t, _ in AUTH1_SETUP.values())
    AUTH1_COMPLETED = sum(c for _, c in AUTH1_SETUP.values())

    AUTH2_SETUP = {"LOW": (1, 0), "HIGH": (1, 0)}
    AUTH2_TOTAL = sum(t for t, _ in AUTH2_SETUP.values())
    AUTH2_COMPLETED = sum(c for _, c in AUTH2_SETUP.values())

    async def _seed_todos(self, client, fake, headers, setup):
        """Create and complete todos from a setup dict. e.g. {"LOW": (3, 2)} = 3 LOW todos, complete 2."""
        for priority, (total, to_complete) in setup.items():
            ids = []
            for _ in range(total):
                resp = await client.post(
                    "/api/v1/todos",
                    json={"title": fake.sentence(nb_words=3), "priority": priority},
                    headers=headers,
                )
                ids.append(resp.json()["id"])
            for todo_id in ids[:to_complete]:
                await client.patch(
                    f"/api/v1/todos/{todo_id}/complete", headers=headers
                )

    @pytest.mark.asyncio
    async def test_stats_with_todos(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        # Arrange
        headers = auth_user["headers"]
        await self._seed_todos(client, fake, headers, self.AUTH1_SETUP)

        # Act
        response = await client.get("/api/v1/todos/stats", headers=headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == self.AUTH1_TOTAL
        assert data["completed"] == self.AUTH1_COMPLETED
        assert data["pending"] == self.AUTH1_TOTAL - self.AUTH1_COMPLETED
        for priority, (total, _) in self.AUTH1_SETUP.items():
            assert data["by_priority"][priority] == total

    @pytest.mark.asyncio
    async def test_stats_empty(self, client: AsyncClient, second_auth_user: dict):
        # Act — second_auth_user has no todos yet
        response = await client.get(
            "/api/v1/todos/stats", headers=second_auth_user["headers"]
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0
        assert data["by_priority"]["LOW"] == 0
        assert data["by_priority"]["MEDIUM"] == 0
        assert data["by_priority"]["HIGH"] == 0

    @pytest.mark.asyncio
    async def test_stats_only_counts_own_todos(
        self,
        client: AsyncClient,
        auth_user: dict,
        second_auth_user: dict,
        fake: Faker,
    ):
        # Arrange — each user seeds their own todos
        await self._seed_todos(client, fake, auth_user["headers"], self.AUTH1_SETUP)
        await self._seed_todos(client, fake, second_auth_user["headers"], self.AUTH2_SETUP)

        # Act — get stats for both users
        user1_stats = await client.get(
            "/api/v1/todos/stats", headers=auth_user["headers"]
        )
        user2_stats = await client.get(
            "/api/v1/todos/stats", headers=second_auth_user["headers"]
        )

        # Assert — user1 stats match AUTH1_SETUP
        assert user1_stats.status_code == 200
        u1 = user1_stats.json()
        assert u1["total"] == self.AUTH1_TOTAL
        assert u1["completed"] == self.AUTH1_COMPLETED
        assert u1["pending"] == self.AUTH1_TOTAL - self.AUTH1_COMPLETED
        for priority, (total, _) in self.AUTH1_SETUP.items():
            assert u1["by_priority"][priority] == total

        # Assert — user2 stats match AUTH2_SETUP
        assert user2_stats.status_code == 200
        u2 = user2_stats.json()
        assert u2["total"] == self.AUTH2_TOTAL
        assert u2["completed"] == self.AUTH2_COMPLETED
        assert u2["pending"] == self.AUTH2_TOTAL - self.AUTH2_COMPLETED
        for priority, (total, _) in self.AUTH2_SETUP.items():
            assert u2["by_priority"][priority] == total

        # Prove they're independent
        assert u1["total"] != u2["total"]

    @pytest.mark.asyncio
    async def test_stats_without_auth(self, client: AsyncClient):
        # Act
        response = await client.get("/api/v1/todos/stats")

        # Assert
        assert response.status_code == 401


# ============================================================
# Full Lifecycle (DB state across chained operations)
# ============================================================


class TestTodoLifecycle:
    """Tests are order-dependent — do NOT reorder. Each test builds on DB state from earlier ones.

    Flow: Create → Read → Update → Complete → Stats (completed)
        → Uncomplete → Stats (pending) → Delete → Verify Gone → Stats (empty)
    """

    # --- Lifecycle constants ---
    INITIAL_PRIORITY = "LOW"
    UPDATED_PRIORITY = "HIGH"

    # --- Runtime state (set by test_1, read by subsequent tests) ---
    _todo_id: str = None
    _headers: dict = None
    _user_id: str = None
    _initial_title: str = None
    _initial_description: str = None
    _updated_title: str = None

    @pytest.mark.asyncio
    async def test_1_create(
        self, client: AsyncClient, auth_user: dict, fake: Faker
    ):
        """Create a todo — store ID + auth for all subsequent tests."""
        # Arrange
        cls = self.__class__
        cls._headers = auth_user["headers"]
        cls._user_id = auth_user["user"]["id"]
        cls._initial_title = fake.sentence(nb_words=3)
        cls._initial_description = fake.paragraph()

        # Act
        response = await client.post(
            "/api/v1/todos",
            json={
                "title": cls._initial_title,
                "description": cls._initial_description,
                "priority": self.INITIAL_PRIORITY,
            },
            headers=cls._headers,
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        cls._todo_id = data["id"]
        assert data["title"] == cls._initial_title
        assert data["description"] == cls._initial_description
        assert data["priority"] == self.INITIAL_PRIORITY
        assert data["status"] == "NOT_STARTED"
        assert data["user_id"] == cls._user_id

    @pytest.mark.asyncio
    async def test_2_read(self, client: AsyncClient):
        """Read the todo — verify all fields match creation."""
        # Act
        response = await client.get(
            f"/api/v1/todos/{self._todo_id}", headers=self._headers
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == self._todo_id
        assert data["title"] == self._initial_title
        assert data["description"] == self._initial_description
        assert data["priority"] == self.INITIAL_PRIORITY
        assert data["status"] == "NOT_STARTED"
        assert data["user_id"] == self._user_id

    @pytest.mark.asyncio
    async def test_3_update(self, client: AsyncClient, fake: Faker):
        """Update title + priority — verify changed fields, unchanged fields preserved."""
        # Arrange
        cls = self.__class__
        cls._updated_title = fake.sentence(nb_words=4)

        # Act
        response = await client.patch(
            f"/api/v1/todos/{self._todo_id}",
            json={"title": cls._updated_title, "priority": self.UPDATED_PRIORITY},
            headers=self._headers,
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == cls._updated_title
        assert data["priority"] == self.UPDATED_PRIORITY
        assert data["description"] == self._initial_description
        assert data["status"] == "NOT_STARTED"
        assert data["user_id"] == self._user_id

    @pytest.mark.asyncio
    async def test_4_toggle_complete(self, client: AsyncClient):
        """Toggle to COMPLETED — verify via response AND GET."""
        # Act
        response = await client.patch(
            f"/api/v1/todos/{self._todo_id}/complete", headers=self._headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "COMPLETED"

        # Verify persisted via GET
        get_response = await client.get(
            f"/api/v1/todos/{self._todo_id}", headers=self._headers
        )
        assert get_response.json()["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_5_stats_after_complete(self, client: AsyncClient):
        """Stats should show 1 total, 1 completed, 0 pending."""
        # Act
        response = await client.get("/api/v1/todos/stats", headers=self._headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["completed"] == 1
        assert data["pending"] == 0
        assert data["by_priority"][self.UPDATED_PRIORITY] == 1

    @pytest.mark.asyncio
    async def test_6_toggle_back(self, client: AsyncClient):
        """Toggle back to NOT_STARTED — verify via response AND GET."""
        # Act
        response = await client.patch(
            f"/api/v1/todos/{self._todo_id}/complete", headers=self._headers
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["status"] == "NOT_STARTED"

        # Verify persisted via GET
        get_response = await client.get(
            f"/api/v1/todos/{self._todo_id}", headers=self._headers
        )
        assert get_response.json()["status"] == "NOT_STARTED"

    @pytest.mark.asyncio
    async def test_7_stats_after_uncomplete(self, client: AsyncClient):
        """Stats should show 1 total, 0 completed, 1 pending."""
        # Act
        response = await client.get("/api/v1/todos/stats", headers=self._headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["completed"] == 0
        assert data["pending"] == 1
        assert data["by_priority"][self.UPDATED_PRIORITY] == 1

    @pytest.mark.asyncio
    async def test_8_delete(self, client: AsyncClient):
        """Delete the todo — verify 204."""
        # Act
        response = await client.delete(
            f"/api/v1/todos/{self._todo_id}", headers=self._headers
        )

        # Assert
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_9_verify_gone(self, client: AsyncClient):
        """GET deleted todo — verify 404 with detail for frontend."""
        # Act
        response = await client.get(
            f"/api/v1/todos/{self._todo_id}", headers=self._headers
        )

        # Assert
        assert response.status_code == 404
        assert response.json().get("detail")

    @pytest.mark.asyncio
    async def test_10_stats_after_delete(self, client: AsyncClient):
        """Stats should be all zeros after deleting the only todo."""
        # Act
        response = await client.get("/api/v1/todos/stats", headers=self._headers)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["completed"] == 0
        assert data["pending"] == 0
        assert data["by_priority"]["LOW"] == 0
        assert data["by_priority"]["MEDIUM"] == 0
        assert data["by_priority"]["HIGH"] == 0
