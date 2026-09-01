import unittest

from app.domain.taxonomy import (
    IdentifierKind,
    TAXONOMY,
    TaxonomyScope,
    ancestors,
    get_node,
    is_a,
    is_valid_type,
    taxonomy_tree,
)


class TaxonomyTests(unittest.TestCase):
    def test_exposes_exact_hierarchy_and_valid_types(self) -> None:
        self.assertTrue(is_valid_type("PERSON_NAME"))
        self.assertTrue(is_a("STUDENT_ID", "IDENTIFIER"))
        self.assertTrue(is_a("STUDENT_ID", "PII"))
        self.assertEqual(ancestors("EMAIL"), ["CONTACT", "PII"])
        self.assertEqual(taxonomy_tree()["version"], "University PII Taxonomy v1")

    def test_preserves_leaf_metadata_without_inventing_parent_values(self) -> None:
        student = get_node("STUDENT_ID")
        self.assertEqual(student.scope, TaxonomyScope.DOMAIN_SPECIFIC)
        self.assertEqual(student.identifier_kind, IdentifierKind.DIRECT)
        self.assertIsNone(TAXONOMY["IDENTIFIER"].scope)
        self.assertIsNone(TAXONOMY["IDENTIFIER"].identifier_kind)

    def test_rejects_unknown_types(self) -> None:
        self.assertFalse(is_valid_type("OTHER"))
        with self.assertRaises(ValueError):
            get_node("MISC")


if __name__ == "__main__":
    unittest.main()
