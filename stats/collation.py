import unicodedata


def locale_sort_key(value: str):
    """Approximates JS's default (locale-aware) String#localeCompare for the
    tiebreak sorts in stats.service.ts, which use it on player/commander
    names. Plain Python string comparison is codepoint-based and puts
    accented letters (e.g. 'É') completely out of alphabetical order —
    stripping diacritics and case-folding gets the same practical ordering
    for the Western names this app deals with."""
    decomposed = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return (stripped.casefold(), value)
