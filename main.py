"""Entry point: lance la boucle de simulation batch."""

from simulation import run


if __name__ == '__main__':
	run(max_monsters=2, batch_mode=True, rest_freq=20)
