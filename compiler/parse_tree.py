"""
Parse Tree Representation and Inspection Utilities.
Provides tree node abstractions, ASCII visualization, and AST extraction for semantic validation.
"""

from typing import Dict, List, Set, Any, Optional
from lark import Tree, Token as LarkToken


class ParseTreeNode:
    """A clean wrapper around Lark parse tree nodes for analysis and visual rendering."""

    def __init__(self, data: str, children: Optional[List[Any]] = None):
        self.data = data
        self.children = children or []

    @classmethod
    def from_lark_tree(cls, tree: Any) -> Any:
        if isinstance(tree, Tree):
            node = cls(tree.data)
            node.children = [cls.from_lark_tree(c) for c in tree.children]
            return node
        elif isinstance(tree, LarkToken):
            return str(tree.value)
        return str(tree)

    def to_ascii_tree(self, prefix: str = "", is_last: bool = True) -> str:
        """Renders an ASCII tree view."""
        connector = "└── " if is_last else "├── "
        result = prefix + connector + str(self.data) + "\n"
        child_prefix = prefix + ("    " if is_last else "│   ")
        count = len(self.children)
        for i, child in enumerate(self.children):
            last = (i == count - 1)
            if isinstance(child, ParseTreeNode):
                result += child.to_ascii_tree(child_prefix, last)
            else:
                c_connector = "└── " if last else "├── "
                result += child_prefix + c_connector + repr(str(child)) + "\n"
        return result

    def to_dict(self) -> Dict[str, Any]:
        """Converts node and subtree to recursive dict format."""
        return {
            "name": self.data,
            "children": [c.to_dict() if isinstance(c, ParseTreeNode) else {"value": str(c)} for c in self.children]
        }


def extract_query_semantics(tree: Tree) -> Dict[str, Any]:
    """
    Extracts semantic entities (tables, columns, clauses, joins, aliases) from a Lark parse tree.
    """
    tables: Set[str] = set()
    columns: Set[str] = set()
    aliases: Dict[str, str] = {}  # alias -> table_name
    clauses: Set[str] = set()

    def visit(node):
        if not isinstance(node, Tree):
            return

        rule = node.data
        if "select" in rule:
            clauses.add("SELECT")
        if "from" in rule:
            clauses.add("FROM")
        if "where" in rule:
            clauses.add("WHERE")
        if "groupby" in rule:
            clauses.add("GROUP BY")
        if "having" in rule:
            clauses.add("HAVING")
        if "orderby" in rule:
            clauses.add("ORDER BY")
        if "limit" in rule:
            clauses.add("LIMIT")
        if "join" in rule:
            clauses.add("JOIN")
        if "insert" in rule:
            clauses.add("INSERT")
        if "update" in rule:
            clauses.add("UPDATE")
        if "delete" in rule:
            clauses.add("DELETE")

        if rule == "table_source":
            # [CNAME, [AS, CNAME]]
            tokens = [c.value for c in node.children if isinstance(c, LarkToken)]
            if len(tokens) >= 1:
                tbl = tokens[0]
                tables.add(tbl.lower())
                if len(tokens) >= 2:
                    aliases[tokens[-1].lower()] = tbl.lower()

        elif rule == "insert_stmt":
            tokens = [c.value for c in node.children if isinstance(c, LarkToken)]
            if tokens:
                tables.add(tokens[0].lower())

        elif rule in ("update_stmt", "delete_stmt"):
            tokens = [c.value for c in node.children if isinstance(c, LarkToken)]
            if tokens:
                tables.add(tokens[0].lower())

        elif rule == "column_ref":
            tokens = [c.value for c in node.children if isinstance(c, LarkToken)]
            if len(tokens) == 1:
                columns.add(tokens[0].lower())
            elif len(tokens) == 2:
                # alias.col or table.col
                columns.add(f"{tokens[0].lower()}.{tokens[1].lower()}")

        for child in node.children:
            visit(child)

    visit(tree)

    return {
        "tables": sorted(tables),
        "columns": sorted(columns),
        "aliases": aliases,
        "clauses": sorted(clauses)
    }
