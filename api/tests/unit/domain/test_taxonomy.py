import pytest

from app.domain.taxonomy import (
    TAXONOMY,
    IdentifierKind,
    TaxonomyScope,
    ancestors,
    get_node,
    is_a,
    is_valid_type,
    taxonomy_tree,
)


def test_exposes_exact_hierarchy_and_valid_types() -> None:
    assert is_valid_type("PERSON_NAME")
    assert is_a("STUDENT_ID", "IDENTIFIER")
    assert is_a("STUDENT_ID", "PII")
    assert ancestors("EMAIL") == ["CONTACT", "PII"]
    assert taxonomy_tree()["version"] == "University PII Taxonomy v1"


def test_preserves_leaf_metadata_without_inventing_parent_values() -> None:
    student = get_node("STUDENT_ID")

    assert student.scope == TaxonomyScope.DOMAIN_SPECIFIC
    assert student.identifier_kind == IdentifierKind.DIRECT
    assert TAXONOMY["IDENTIFIER"].scope is None
    assert TAXONOMY["IDENTIFIER"].identifier_kind is None


def test_rejects_unknown_types() -> None:
    assert not is_valid_type("OTHER")
    with pytest.raises(ValueError, match="Unknown canonical entity type: MISC"):
        get_node("MISC")
