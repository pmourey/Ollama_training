"""Shared mutable simulation state (avoids circular imports).

In batch mode, uprint writes messages to a rotating log file so rounds can be
reviewed later. The log file defaults to data/combat.log but can be overridden
by setting GAME_LOG_PATH in environment if desired.
"""
from pathlib import Path
from datetime import datetime
import os

BATCH_MODE: bool = True
BACK_TO_TOWN_FREQ: int = 100
spells_cast: list[dict[str, int]] = []
killed_by_level: list[dict[str, int]] = []

# Default log path
_LOG_PATH = Path(os.environ.get('GAME_LOG_PATH', 'data/combat.log'))

# Ensure parent directory exists
_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _write_log_line(line: str) -> None:
	with _LOG_PATH.open('a', encoding='utf-8') as f:
		f.write(line + '\n')


def uprint(msg: str = '') -> None:
	"""Print to stdout in interactive mode; append to log in batch mode."""
	if not BATCH_MODE:
		print(msg)
	else:
		# Prefix each message with ISO timestamp for easier parsing
		ts = datetime.utcnow().isoformat() + 'Z'
		for line in str(msg).splitlines() or ['']:
			_write_log_line(f'[{ts}] {line}')
