"""Shared mutable simulation state (avoids circular imports)."""

BATCH_MODE: bool = True
BACK_TO_TOWN_FREQ: int = 100
spells_cast: list[dict[str, int]] = []
killed_by_level: list[dict[str, int]] = []


def uprint(msg: str = '') -> None:
	if not BATCH_MODE:
		print(msg)
