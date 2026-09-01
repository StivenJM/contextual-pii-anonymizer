from dataclasses import dataclass
from enum import StrEnum


class TaxonomyScope(StrEnum):
    CORE = "CORE"
    DOMAIN_SPECIFIC = "DOMAIN_SPECIFIC"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"


class IdentifierKind(StrEnum):
    DIRECT = "DIRECT"
    INDIRECT = "INDIRECT"


@dataclass(frozen=True)
class TaxonomyNode:
    name: str
    parent: str | None
    scope: TaxonomyScope | None = None
    identifier_kind: IdentifierKind | None = None


_NODES = (
    TaxonomyNode("PII", None),
    TaxonomyNode("PERSON", "PII"),
    TaxonomyNode("PERSON_NAME", "PERSON", TaxonomyScope.CORE, IdentifierKind.DIRECT),
    TaxonomyNode("CONTACT", "PII"),
    TaxonomyNode("EMAIL", "CONTACT", TaxonomyScope.CORE, IdentifierKind.DIRECT),
    TaxonomyNode("PHONE", "CONTACT", TaxonomyScope.CORE, IdentifierKind.DIRECT),
    TaxonomyNode("DIGITAL_IDENTITY", "PII"),
    TaxonomyNode("USERNAME", "DIGITAL_IDENTITY", TaxonomyScope.CORE, IdentifierKind.DIRECT),
    TaxonomyNode("PERSONAL_URL", "DIGITAL_IDENTITY", TaxonomyScope.CORE, IdentifierKind.DIRECT),
    TaxonomyNode("IDENTIFIER", "PII"),
    TaxonomyNode("NATIONAL_ID", "IDENTIFIER", TaxonomyScope.CORE, IdentifierKind.DIRECT),
    TaxonomyNode("STUDENT_ID", "IDENTIFIER", TaxonomyScope.DOMAIN_SPECIFIC, IdentifierKind.DIRECT),
    TaxonomyNode("GEOGRAPHIC", "PII"),
    TaxonomyNode("STREET_ADDRESS", "GEOGRAPHIC", TaxonomyScope.CORE, IdentifierKind.DIRECT),
    TaxonomyNode("LOCATION", "GEOGRAPHIC", TaxonomyScope.CONTEXT_DEPENDENT, IdentifierKind.INDIRECT),
    TaxonomyNode("NATIONALITY", "GEOGRAPHIC", TaxonomyScope.CONTEXT_DEPENDENT, IdentifierKind.INDIRECT),
    TaxonomyNode("DEMOGRAPHIC", "PII"),
    TaxonomyNode("AGE", "DEMOGRAPHIC", TaxonomyScope.CONTEXT_DEPENDENT, IdentifierKind.INDIRECT),
    TaxonomyNode("TEMPORAL", "PII"),
    TaxonomyNode("DATE", "TEMPORAL", TaxonomyScope.CONTEXT_DEPENDENT, IdentifierKind.INDIRECT),
    TaxonomyNode("AFFILIATION", "PII"),
    TaxonomyNode(
        "EDUCATIONAL_AFFILIATION",
        "AFFILIATION",
        TaxonomyScope.DOMAIN_SPECIFIC,
        IdentifierKind.INDIRECT,
    ),
    TaxonomyNode(
        "EMPLOYMENT_AFFILIATION",
        "AFFILIATION",
        TaxonomyScope.CONTEXT_DEPENDENT,
        IdentifierKind.INDIRECT,
    ),
)

TAXONOMY_VERSION = "University PII Taxonomy v1"
TAXONOMY = {node.name: node for node in _NODES}


def get_node(name: str) -> TaxonomyNode:
    try:
        return TAXONOMY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown canonical entity type: {name}") from exc


def is_valid_type(name: str) -> bool:
    return name in TAXONOMY


def ancestors(name: str, *, include_self: bool = False) -> list[str]:
    node = get_node(name)
    result = [node.name] if include_self else []
    while node.parent is not None:
        result.append(node.parent)
        node = TAXONOMY[node.parent]
    return result


def is_a(child: str, parent: str) -> bool:
    return parent in ancestors(child, include_self=True)


def depth(name: str) -> int:
    return len(ancestors(name))


def taxonomy_tree() -> dict[str, object]:
    def serialize(name: str) -> dict[str, object]:
        node = TAXONOMY[name]
        children = [item.name for item in _NODES if item.parent == name]
        return {
            "name": node.name,
            "scope": node.scope.value if node.scope else None,
            "identifier_kind": node.identifier_kind.value if node.identifier_kind else None,
            "children": [serialize(child) for child in children],
        }

    return {"version": TAXONOMY_VERSION, "root": serialize("PII")}
