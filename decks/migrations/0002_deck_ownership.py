import uuid

import django.db.models.deletion
from django.db import migrations, models


def clear_deck_cards(apps, schema_editor):
    """DeckCard was global-per-commander with no owner recorded anywhere, so
    there's no ownership data to backfill — the only two decks that existed
    (Queen Marchesa, Gonti) get re-imported with an explicit owner right after
    this migration via the updated import_moxfield_decks command."""
    DeckCard = apps.get_model("decks", "DeckCard")
    DeckCard.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("commanders", "0001_initial"),
        ("players", "0001_initial"),
        ("decks", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Deck",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.TextField(blank=True, null=True)),
                ("source", models.TextField(default="manual")),
                ("moxfield_deck_id", models.TextField(blank=True, null=True)),
                ("moxfield_url", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "commander",
                    models.ForeignKey(
                        db_column="commander_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="decks",
                        to="commanders.commander",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        db_column="owner_id",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="decks",
                        to="players.player",
                    ),
                ),
            ],
            options={
                "db_table": "decks",
                "indexes": [
                    models.Index(fields=["owner"], name="idx_decks_owner_id"),
                    models.Index(fields=["commander"], name="idx_decks_commander_id"),
                ],
            },
        ),
        migrations.RunPython(clear_deck_cards, migrations.RunPython.noop),
        migrations.RemoveIndex(
            model_name="deckcard",
            name="idx_deck_cards_commander_id",
        ),
        migrations.RemoveField(
            model_name="deckcard",
            name="commander",
        ),
        migrations.AddField(
            model_name="deckcard",
            name="deck",
            field=models.ForeignKey(
                db_column="deck_id",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cards",
                to="decks.deck",
            ),
        ),
        # Safe because clear_deck_cards emptied the table above — no existing
        # NULLs to violate the new NOT NULL constraint.
        migrations.AlterField(
            model_name="deckcard",
            name="deck",
            field=models.ForeignKey(
                db_column="deck_id",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cards",
                to="decks.deck",
            ),
        ),
        migrations.AddIndex(
            model_name="deckcard",
            index=models.Index(fields=["deck"], name="idx_deck_cards_deck_id"),
        ),
    ]
