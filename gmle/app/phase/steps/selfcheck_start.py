"""Selfcheck Start phase (spec 12.1)."""

from __future__ import annotations

from typing import Any, Dict

from gmle.app.infra.errors import InfraError
from gmle.app.infra.lock import acquire_lock
from .checks.anki_connect import check_anki_connect
from .checks.base_fetch import check_base_fetch
from .checks.note_type_fields import check_note_type_fields
from .checks.one_card_per_note import check_one_card_per_note
from .checks.id_uniqueness import check_id_uniqueness
from .checks.items_parse import check_items_parse
from .checks.paths_deck import check_paths_deck


def execute(context: Dict[str, Any]) -> None:
    """Run selfcheck start (spec 12.1 must-pass set)."""
    paths = context["paths"]
    space_id = context["space_id"]
    deck_bank = context["deck_bank"]

    # Lock取得（stale判定含む）
    # 既にロックが取得されている場合はスキップ（run関数から呼ばれる場合）
    if not paths["lock"].exists():
        try:
            acquire_lock(paths["lock"])
        except InfraError as exc:
            raise InfraError(f"lock acquisition failed: {paths['lock']}") from exc

    # AnkiConnect疎通（version）
    check_anki_connect()

    # BASE取得可能（findNotes + notesInfo）
    base_note_ids = check_base_fetch(deck_bank)

    # note type / fields整合
    check_note_type_fields()

    # 1ノート=1カード検証可能（cardsInfo等）
    check_one_card_per_note(base_note_ids)

    # I7（ID一意）が成立
    check_id_uniqueness(base_note_ids)

    # items.json が存在する場合パース可能
    check_items_parse(paths["items"])

    # Sx1〜Sx4 のパス/デッキ解決が成功
    check_paths_deck(paths, space_id, deck_bank)
