import uuid

from django.test import TestCase

from players.models import Player
from players.services import (
    find_player_by_identifier,
    get_family_ids,
    get_player_identity_map,
    is_uuid,
    resolve_canonical_player,
)


class IsUuidTests(TestCase):
    def test_valid_uuid(self):
        self.assertTrue(is_uuid(str(uuid.uuid4())))

    def test_invalid_uuid(self):
        self.assertFalse(is_uuid("not-a-uuid"))

    def test_none(self):
        self.assertFalse(is_uuid(None))


class FindPlayerByIdentifierTests(TestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Alice")

    def test_lookup_by_uuid(self):
        found = find_player_by_identifier(str(self.player.id))
        self.assertEqual(found.id, self.player.id)

    def test_lookup_by_name_case_insensitive(self):
        found = find_player_by_identifier("aLiCe")
        self.assertEqual(found.id, self.player.id)

    def test_lookup_by_name_trims_whitespace(self):
        found = find_player_by_identifier("  Alice  ")
        self.assertEqual(found.id, self.player.id)

    def test_unknown_name_returns_none(self):
        self.assertIsNone(find_player_by_identifier("Nobody"))

    def test_unknown_uuid_returns_none(self):
        self.assertIsNone(find_player_by_identifier(str(uuid.uuid4())))

    def test_duplicate_names_oldest_wins(self):
        # created_at is auto_now_add, so insertion order determines "oldest".
        newer = Player.objects.create(id=uuid.uuid4(), name="Alice")
        found = find_player_by_identifier("Alice")
        self.assertEqual(found.id, self.player.id)
        self.assertNotEqual(found.id, newer.id)


class ResolveCanonicalPlayerTests(TestCase):
    def setUp(self):
        self.canonical = Player.objects.create(id=uuid.uuid4(), name="Canonical")
        self.alias = Player.objects.create(id=uuid.uuid4(), name="Alias", merged_into=self.canonical)

    def test_non_alias_resolves_to_itself(self):
        resolved = resolve_canonical_player(str(self.canonical.id))
        self.assertEqual(resolved.id, self.canonical.id)

    def test_alias_resolves_to_canonical(self):
        resolved = resolve_canonical_player(str(self.alias.id))
        self.assertEqual(resolved.id, self.canonical.id)

    def test_alias_resolves_by_name_too(self):
        resolved = resolve_canonical_player("Alias")
        self.assertEqual(resolved.id, self.canonical.id)

    def test_unknown_identifier_returns_none(self):
        self.assertIsNone(resolve_canonical_player("Nobody"))


class GetFamilyIdsTests(TestCase):
    def test_includes_canonical_and_aliases(self):
        canonical = Player.objects.create(id=uuid.uuid4(), name="Canonical")
        alias1 = Player.objects.create(id=uuid.uuid4(), name="Alias1", merged_into=canonical)
        alias2 = Player.objects.create(id=uuid.uuid4(), name="Alias2", merged_into=canonical)
        other = Player.objects.create(id=uuid.uuid4(), name="Unrelated")

        family = get_family_ids(canonical.id)

        self.assertIn(canonical.id, family)
        self.assertIn(alias1.id, family)
        self.assertIn(alias2.id, family)
        self.assertNotIn(other.id, family)
        self.assertEqual(len(family), 3)

    def test_no_aliases_returns_just_itself(self):
        solo = Player.objects.create(id=uuid.uuid4(), name="Solo")
        self.assertEqual(get_family_ids(solo.id), [solo.id])


class GetPlayerIdentityMapTests(TestCase):
    def test_maps_aliases_to_canonical_and_names(self):
        canonical = Player.objects.create(id=uuid.uuid4(), name="  Canonical  ")
        alias = Player.objects.create(id=uuid.uuid4(), name="Alias", merged_into=canonical)

        id_map, name_map = get_player_identity_map()

        self.assertEqual(id_map[canonical.id], canonical.id)
        self.assertEqual(id_map[alias.id], canonical.id)
        # Name is trimmed, and only the canonical row contributes a name.
        self.assertEqual(name_map[canonical.id], "Canonical")
        self.assertNotIn(alias.id, name_map)
