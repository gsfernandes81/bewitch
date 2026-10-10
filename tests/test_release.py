"""What a release is made of: one version, said the same way twice."""

from __future__ import annotations

import tomllib
from pathlib import Path

import bewitch

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_the_package_says_the_version_pyproject_releases():
    # The release workflow publishes whatever pyproject.toml says; the gallery
    # header prints __version__. A bump to one alone ships a wheel that names
    # itself wrongly.
    released = tomllib.loads(PYPROJECT.read_text())["project"]["version"]
    assert bewitch.__version__ == released
