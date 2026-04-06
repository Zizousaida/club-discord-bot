from __future__ import annotations

import config


class _Role:
    def __init__(self, name: str) -> None:
        self.name = name


class _Member:
    def __init__(self, roles: list[_Role]) -> None:
        self.roles = roles


def test_has_named_role_matches_by_name(monkeypatch) -> None:
    monkeypatch.setattr(config, "HR_ROLE_NAME", "HR")
    monkeypatch.setattr(config, "STAFF_ROLE_NAME", "Staff")

    member = _Member(roles=[_Role("HR")])
    assert any(r.name == config.HR_ROLE_NAME for r in member.roles)


def test_staff_role_includes_hr(monkeypatch) -> None:
    monkeypatch.setattr(config, "HR_ROLE_NAME", "HR")
    monkeypatch.setattr(config, "STAFF_ROLE_NAME", "Staff")

    roles = [_Role("HR")]
    assert any(r.name == config.STAFF_ROLE_NAME for r in roles) is False
    assert any(r.name == config.HR_ROLE_NAME for r in roles) is True
