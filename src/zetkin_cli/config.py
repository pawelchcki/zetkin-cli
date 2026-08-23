"""Profile configuration kept separate from secrets and tokens."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_path

from .errors import ZetkinConfigError

DEFAULT_BASE_URL = "https://api.zetk.in"


@dataclass(frozen=True, slots=True)
class Profile:
    name: str
    base_url: str = DEFAULT_BASE_URL
    redirect_uri: str | None = None


class ConfigStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or user_config_path("zetkin-cli") / "config.toml"

    def _read(self) -> dict[str, object]:
        if not self.path.exists():
            return {}
        try:
            return tomllib.loads(self.path.read_text())
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ZetkinConfigError(f"Could not read {self.path}: {exc}") from exc

    def names(self) -> list[str]:
        profiles = self._read().get("profiles", {})
        return sorted(profiles) if isinstance(profiles, dict) else []

    def default_name(self) -> str:
        configured = self._read().get("default_profile")
        return str(configured) if configured else "default"

    def get(self, name: str | None = None) -> Profile:
        data = self._read()
        selected = (
            name
            or os.getenv("ZETKIN_PROFILE")
            or str(data.get("default_profile", "default"))
        )
        profiles = data.get("profiles", {})
        raw = profiles.get(selected, {}) if isinstance(profiles, dict) else {}
        if not isinstance(raw, dict):
            raise ZetkinConfigError(f"Profile {selected!r} is invalid")
        return Profile(
            name=selected,
            base_url=os.getenv("ZETKIN_BASE_URL")
            or str(raw.get("base_url", DEFAULT_BASE_URL)),
            redirect_uri=os.getenv("ZETKIN_REDIRECT_URI")
            or (str(raw["redirect_uri"]) if raw.get("redirect_uri") else None),
        )

    def add(self, profile: Profile) -> None:
        data = self._read()
        default = str(data.get("default_profile", "default"))
        profiles = data.get("profiles", {})
        if not isinstance(profiles, dict):
            profiles = {}
        profiles[profile.name] = {
            "base_url": profile.base_url,
            **({"redirect_uri": profile.redirect_uri} if profile.redirect_uri else {}),
        }
        self._write(default, profiles)

    def set_default(self, name: str) -> None:
        data = self._read()
        profiles = data.get("profiles", {})
        if not isinstance(profiles, dict) or name not in profiles:
            raise ZetkinConfigError(f"Profile {name!r} does not exist")
        self._write(name, profiles)

    def _write(self, default: str, profiles: dict[str, object]) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        lines = [f'default_profile = "{_escape(default)}"', ""]
        for name in sorted(profiles):
            raw = profiles[name]
            if not isinstance(raw, dict):
                continue
            lines.extend([f'[profiles."{_escape(name)}"]'])
            for key in ("base_url", "redirect_uri"):
                value = raw.get(key)
                if value:
                    lines.append(f'{key} = "{_escape(str(value))}"')
            lines.append("")
        self.path.write_text("\n".join(lines))
        self.path.chmod(0o600)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
