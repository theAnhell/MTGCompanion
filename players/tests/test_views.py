import uuid

from rest_framework.test import APITestCase

from players.models import Player


class PlayerListViewTests(APITestCase):
    def setUp(self):
        self.active = Player.objects.create(id=uuid.uuid4(), name="Bea")
        self.alias = Player.objects.create(id=uuid.uuid4(), name="Old Bea", merged_into=self.active)

    def test_list_excludes_merged_by_default(self):
        response = self.client.get("/api/v1/players")
        self.assertEqual(response.status_code, 200)
        names = [p["name"] for p in response.data]
        self.assertIn("Bea", names)
        self.assertNotIn("Old Bea", names)

    def test_list_includes_merged_when_requested(self):
        response = self.client.get("/api/v1/players?includeMerged=true")
        self.assertEqual(response.status_code, 200)
        names = [p["name"] for p in response.data]
        self.assertIn("Old Bea", names)


class PlayerDetailViewTests(APITestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Cho")

    def test_get_by_uuid(self):
        response = self.client.get(f"/api/v1/players/{self.player.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["name"], "Cho")

    def test_get_by_name(self):
        response = self.client.get("/api/v1/players/Cho")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data["id"]), str(self.player.id))

    def test_not_found_reshapes_error_body(self):
        response = self.client.get(f"/api/v1/players/{uuid.uuid4()}")
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)
