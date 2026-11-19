import uuid

from django.test import TestCase

from commanders.models import Commander
from decks.models import Deck, DeckCard, RetiredDeck
from decks.services import (
    add_retired_deck,
    get_deck,
    get_retired_commander_id_set,
    list_player_decks,
    list_retired_decks_with_commander_info,
    remove_retired_deck,
    replace_deck_cards,
)
from players.models import Player


class RetiredDeckServiceTests(TestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")

    def test_add_retired_deck_creates_row(self):
        add_retired_deck(self.player.id, self.commander.id)
        self.assertTrue(
            RetiredDeck.objects.filter(player=self.player, commander=self.commander).exists()
        )

    def test_add_retired_deck_is_idempotent(self):
        add_retired_deck(self.player.id, self.commander.id)
        add_retired_deck(self.player.id, self.commander.id)
        self.assertEqual(
            RetiredDeck.objects.filter(player=self.player, commander=self.commander).count(), 1
        )

    def test_remove_retired_deck(self):
        add_retired_deck(self.player.id, self.commander.id)
        remove_retired_deck(self.player.id, self.commander.id)
        self.assertFalse(RetiredDeck.objects.filter(player=self.player).exists())

    def test_get_retired_commander_id_set_scoped_to_family(self):
        other_player = Player.objects.create(id=uuid.uuid4(), name="Other")
        add_retired_deck(self.player.id, self.commander.id)
        result = get_retired_commander_id_set([self.player.id])
        self.assertEqual(result, {self.commander.id})
        self.assertEqual(get_retired_commander_id_set([other_player.id]), set())

    def test_get_retired_commander_id_set_empty_family_returns_empty(self):
        self.assertEqual(get_retired_commander_id_set([]), set())

    def test_list_retired_decks_with_commander_info_orders_by_commander_name(self):
        c2 = Commander.objects.create(id=uuid.uuid4(), name="Aang, Swift Savior")
        add_retired_deck(self.player.id, self.commander.id)
        add_retired_deck(self.player.id, c2.id)

        rows = list(list_retired_decks_with_commander_info([self.player.id]))

        self.assertEqual([r.commander.name for r in rows], ["Aang, Swift Savior", "Queen Marchesa"])


class ReplaceDeckCardsTests(TestCase):
    def setUp(self):
        self.player = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.player, commander=self.commander)

    def test_replace_inserts_rows(self):
        replace_deck_cards(self.deck.id, [{"card_name": "Sol Ring", "quantity": 1}])
        self.assertEqual(DeckCard.objects.filter(deck=self.deck).count(), 1)

    def test_replace_is_a_full_replace_not_a_merge(self):
        replace_deck_cards(self.deck.id, [{"card_name": "Sol Ring", "quantity": 1}])
        replace_deck_cards(self.deck.id, [{"card_name": "Arcane Signet", "quantity": 1}])

        cards = list(DeckCard.objects.filter(deck=self.deck).values_list("card_name", flat=True))
        self.assertEqual(cards, ["Arcane Signet"])

    def test_replace_with_empty_rows_clears_deck(self):
        replace_deck_cards(self.deck.id, [{"card_name": "Sol Ring", "quantity": 1}])
        replace_deck_cards(self.deck.id, [])
        self.assertEqual(DeckCard.objects.filter(deck=self.deck).count(), 0)


class ListPlayerDecksAndGetDeckTests(TestCase):
    def setUp(self):
        self.owner = Player.objects.create(id=uuid.uuid4(), name="Owner")
        self.other_owner = Player.objects.create(id=uuid.uuid4(), name="Other")
        self.commander = Commander.objects.create(id=uuid.uuid4(), name="Queen Marchesa")
        self.deck = Deck.objects.create(id=uuid.uuid4(), owner=self.owner, commander=self.commander)
        Deck.objects.create(id=uuid.uuid4(), owner=self.other_owner, commander=self.commander)

    def test_list_player_decks_scoped_to_owner(self):
        decks = list(list_player_decks(self.owner.id))
        self.assertEqual(len(decks), 1)
        self.assertEqual(decks[0].id, self.deck.id)

    def test_get_deck_returns_none_for_missing(self):
        self.assertIsNone(get_deck(uuid.uuid4()))

    def test_get_deck_returns_deck_with_prefetched_cards(self):
        DeckCard.objects.create(deck=self.deck, card_name="Sol Ring", quantity=1)
        found = get_deck(self.deck.id)
        self.assertEqual(found.id, self.deck.id)
        self.assertEqual(len(found.cards.all()), 1)
