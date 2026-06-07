from __future__ import annotations

from pathlib import Path

import pytest

from .data import example_ed25519_signer, example_eip712_signer


@pytest.fixture
def eip712_signer():
    return example_eip712_signer()


@pytest.fixture
def ed25519_signer():
    return example_ed25519_signer()


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "tests" / "cross-runtime" / "fixtures"
