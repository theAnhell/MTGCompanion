import re

# Matches Moxfield's plain-text export lines, e.g.:
#   1 Queen Marchesa (SLD) 2688 *F*
#   1 Chaos Warp (PLST) C17-131
#   2 Mountain (BRO) 284
LINE_PATTERN = re.compile(r"^(\d+)\s+(.+?)\s+\(([A-Za-z0-9]+)\)\s+(\S+?)(\s+\*F\*)?$")


def parse_moxfield_export(text: str) -> list[dict]:
    cards = []
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        match = LINE_PATTERN.match(line)
        if not match:
            print(f'Skipping unrecognized decklist line: "{line}"')
            continue
        quantity, card_name, set_code, collector_number, foil_marker = match.groups()
        cards.append(
            {
                "quantity": int(quantity),
                "cardName": card_name.strip(),
                "setCode": set_code.upper(),
                "collectorNumber": collector_number,
                "isFoil": bool(foil_marker),
            }
        )
    return cards


def normalize_card_name(name: str) -> str:
    """Normalizes Moxfield's " / " split-card separator to Scryfall/MythicTrack's
    " // " for name matching."""
    return re.sub(r"\s+/\s+", " // ", name).strip()
