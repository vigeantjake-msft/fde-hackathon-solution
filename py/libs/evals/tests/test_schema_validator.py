# Copyright (c) Microsoft. All rights reserved.
"""Tests for the schema validator."""

from ms.evals.validators.schema_validator import SchemaViolation
from ms.evals.validators.schema_validator import validate_response_schema


def _valid_response(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "ticket_id": "INC-0001",
        "category": "Network & Connectivity",
        "priority": "P3",
        "assigned_team": "Network Operations",
        "needs_escalation": False,
        "missing_information": [],
        "next_best_action": "Investigate the network issue.",
        "remediation_steps": ["Step 1", "Step 2"],
    }
    base.update(overrides)
    return base


class TestValidResponse:
    def test_valid_response_has_no_violations(self):
        violations = validate_response_schema(_valid_response())
        assert violations == []

    def test_valid_with_missing_info_items(self):
        resp = _valid_response(missing_information=["device_info", "error_message"])
        violations = validate_response_schema(resp)
        assert violations == []

    def test_valid_with_escalation_true(self):
        resp = _valid_response(needs_escalation=True)
        violations = validate_response_schema(resp)
        assert violations == []

    def test_all_categories_valid(self):
        for cat in (
            "Access & Authentication",
            "Hardware & Peripherals",
            "Network & Connectivity",
            "Software & Applications",
            "Security & Compliance",
            "Data & Storage",
            "General Inquiry",
            "Not a Support Ticket",
        ):
            violations = validate_response_schema(_valid_response(category=cat))
            assert violations == [], f"Category {cat!r} should be valid"

    def test_all_priorities_valid(self):
        for pri in ("P1", "P2", "P3", "P4"):
            violations = validate_response_schema(_valid_response(priority=pri))
            assert violations == [], f"Priority {pri!r} should be valid"


class TestMissingFields:
    def test_missing_ticket_id(self):
        resp = _valid_response()
        del resp["ticket_id"]
        violations = validate_response_schema(resp)
        assert any(v.field == "ticket_id" for v in violations)

    def test_missing_category(self):
        resp = _valid_response()
        del resp["category"]
        violations = validate_response_schema(resp)
        assert any(v.field == "category" for v in violations)

    def test_missing_multiple_fields(self):
        resp = {"ticket_id": "INC-0001"}
        violations = validate_response_schema(resp)
        assert len(violations) >= 5

    def test_empty_response(self):
        violations = validate_response_schema({})
        assert len(violations) == len(
            (
                "ticket_id",
                "category",
                "priority",
                "assigned_team",
                "needs_escalation",
                "missing_information",
                "next_best_action",
                "remediation_steps",
            )
        )


class TestInvalidValues:
    def test_invalid_category(self):
        violations = validate_response_schema(_valid_response(category="Invalid Category"))
        assert any(v.field == "category" for v in violations)

    def test_invalid_priority(self):
        violations = validate_response_schema(_valid_response(priority="P5"))
        assert any(v.field == "priority" for v in violations)

    def test_invalid_team(self):
        violations = validate_response_schema(_valid_response(assigned_team="Unknown Team"))
        assert any(v.field == "assigned_team" for v in violations)

    def test_invalid_missing_info_item(self):
        violations = validate_response_schema(_valid_response(missing_information=["invalid_field"]))
        assert any(v.field == "missing_information" for v in violations)

    def test_category_wrong_type(self):
        violations = validate_response_schema(_valid_response(category=123))
        assert any(v.field == "category" for v in violations)

    def test_priority_wrong_type(self):
        violations = validate_response_schema(_valid_response(priority=3))
        assert any(v.field == "priority" for v in violations)

    def test_missing_info_not_list(self):
        violations = validate_response_schema(_valid_response(missing_information="device_info"))
        assert any(v.field == "missing_information" for v in violations)

    def test_remediation_steps_not_list(self):
        violations = validate_response_schema(_valid_response(remediation_steps="Step 1"))
        assert any(v.field == "remediation_steps" for v in violations)

    def test_next_best_action_empty(self):
        violations = validate_response_schema(_valid_response(next_best_action=""))
        assert any(v.field == "next_best_action" for v in violations)

    def test_escalation_invalid_string(self):
        violations = validate_response_schema(_valid_response(needs_escalation="maybe"))
        assert any(v.field == "needs_escalation" for v in violations)


class TestBooleanTolerance:
    def test_escalation_string_true_accepted(self):
        violations = validate_response_schema(_valid_response(needs_escalation="true"))
        escalation_violations = [v for v in violations if v.field == "needs_escalation"]
        assert escalation_violations == []

    def test_escalation_string_false_accepted(self):
        violations = validate_response_schema(_valid_response(needs_escalation="false"))
        escalation_violations = [v for v in violations if v.field == "needs_escalation"]
        assert escalation_violations == []

    def test_escalation_int_0_accepted(self):
        violations = validate_response_schema(_valid_response(needs_escalation=0))
        escalation_violations = [v for v in violations if v.field == "needs_escalation"]
        assert escalation_violations == []

    def test_escalation_int_1_accepted(self):
        violations = validate_response_schema(_valid_response(needs_escalation=1))
        escalation_violations = [v for v in violations if v.field == "needs_escalation"]
        assert escalation_violations == []


class TestSchemaViolationEquality:
    def test_equal_violations(self):
        v1 = SchemaViolation("field", "message")
        v2 = SchemaViolation("field", "message")
        assert v1 == v2

    def test_unequal_violations(self):
        v1 = SchemaViolation("field1", "message")
        v2 = SchemaViolation("field2", "message")
        assert v1 != v2

    def test_violation_repr(self):
        v = SchemaViolation("category", "Invalid value")
        assert "category" in repr(v)
        assert "Invalid value" in repr(v)

    def test_not_equal_to_other_type(self):
        v = SchemaViolation("field", "message")
        assert v != "not a violation"
