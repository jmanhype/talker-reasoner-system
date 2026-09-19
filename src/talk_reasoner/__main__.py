"""Module entry point for the local Talker-Reasoner fixture CLI."""

from collections.abc import Sequence

from talk_reasoner.cli import main

__all__ = ["main"]
DEFAULT_ARGV: Sequence[str] | None = None


def _entrypoint(argv: Sequence[str] | None = None) -> int:
    """Delegate arguments to the typed CLI boundary without extra behavior."""
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(_entrypoint(DEFAULT_ARGV))
