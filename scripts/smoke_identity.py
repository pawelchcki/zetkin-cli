#!/usr/bin/env python3
"""Opt-in live identity smoke test; never performs organization reads or writes."""

from __future__ import annotations

from zetkin_cli import ZetkinClient


def main() -> None:
    with ZetkinClient.from_env() as client:
        user = client.v1.current_user()
        print(f"Authenticated as user {user.id}")


if __name__ == "__main__":
    main()
