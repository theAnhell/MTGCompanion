import re

# Matches Moxfield's plain-text export lines, e.g.:
#   1 Queen Marchesa (SLD) 2688 *F*
#   1 Chaos Warp (PLST) C17-131
#   2 Mountain (BRO) 284
#   1 Nahiri's Resolve (MAT) 137 *E*
# The trailing marker isn't just *F* — Moxfield also emits *E* (etched foil)
# and other finish markers. Matching any `*...*` here (rather than only *F*)
# matters: an unmatched line is dropped from the deck entirely, not just
# mis-tagged, so being permissive here avoids silently losing real cards.
LINE_PATTERN = re.compile(r"^(\d+)\s+(.+?)\s+\(([A-Za-z0-9]+)\)\s+(\S+?)(\s+\*[A-Za-z0-9]+\*)?$")
FOIL_MARKERS = {"F", "E"}

# A "Sideboard"/"Maybeboard"/"Considering" heading marks the end of the
# mainboard in Moxfield's plain-text export; anything after it isn't part of
# the deck and must not be counted, even though its lines otherwise match
# LINE_PATTERN just fine.
BOARD_BREAK_HEADINGS = {"SIDEBOARD", "MAYBEBOARD", "CONSIDERING"}


def parse_moxfield_export(text: str) -> list[dict]:
    cards = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if line.rstrip(":").upper() in BOARD_BREAK_HEADINGS:
            break
        match = LINE_PATTERN.match(line)
        if not match:
            print(f'Skipping unrecognized decklist line: "{line}"')
            continue
        quantity, card_name, set_code, collector_number, marker = match.groups()
        is_foil = bool(marker) and marker.strip().strip("*").upper() in FOIL_MARKERS
        cards.append(
            {
                "quantity": int(quantity),
                "cardName": card_name.strip(),
                "setCode": set_code.upper(),
                "collectorNumber": collector_number,
                "isFoil": is_foil,
            }
        )
    return cards


def normalize_card_name(name: str) -> str:
    """Normalizes Moxfield's " / " split-card separator to Scryfall/MythicTrack's
    " // " for name matching."""
    return re.sub(r"\s+/\s+", " // ", name).strip()


def extract_moxfield_deck_id(url: str) -> str | None:
    match = re.search(r"/decks/([^/?#]+)", url)
    return match.group(1) if match else None


def is_commander_card(card_name: str, commander_name: str) -> bool:
    """A card is the commander if its (normalized) name matches the commander's
    own name, front-face-only for split/MDFC cards."""
    normalized_card = normalize_card_name(card_name).lower()
    normalized_commander = commander_name.strip().lower()
    if normalized_card == normalized_commander:
        return True
    front_face = normalized_card.split(" // ")[0]
    return front_face == normalized_commander
