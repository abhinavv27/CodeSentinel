import os
import ast
from typing import Dict, List, Set
from pathlib import Path
import structlog

logger = structlog.get_logger()

class DependencyService:
    """
    Analyzes repository structure to identify file dependencies.
    Used for providing architectural context during reviews.
    """

    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.file_dependencies: Dict[str, Set[str]] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = {}

    def build_graph(self):
        """Walks the root path and builds a map of file imports."""
        logger.info("building_dependency_graph", root=str(self.root_path))
        
        for p in self.root_path.rglob("*.py"):
            try:
                rel_path = str(p.relative_to(self.root_path))
                imports = self._extract_imports(p)
                
                if rel_path not in self.file_dependencies:
                    self.file_dependencies[rel_path] = set()
                
                for imp in imports:
                    target_path = self._resolve_import(p, imp)
                    if target_path:
                        self.file_dependencies[rel_path].add(target_path)
                        if target_path not in self.reverse_dependencies:
                            self.reverse_dependencies[target_path] = set()
                        self.reverse_dependencies[target_path].add(rel_path)
            except Exception as e:
                logger.warning("dependency_analysis_failed", file=str(p), error=str(e))

    def get_impacted_files(self, changed_file: str) -> List[str]:
        """Returns files that depend on the changed file."""
        return list(self.reverse_dependencies.get(changed_file, set()))

    def _extract_imports(self, file_path: Path) -> List[str]:
        """Extracts import strings from a Python file using AST."""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read())
            
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            return imports
        except Exception:
            return []

    def _resolve_import(self, current_file: Path, import_name: str) -> str | None:
        """Heuristically resolves an import name to a file path within the repo."""
        # This is a simplified resolver for demo purposes.
        # In a real system, we'd check sys.path, __init__.py, etc.
        parts = import_name.split(".")
        potential_path = self.root_path / Path(*parts)
        
        # Check for directory/module
        if (potential_path / "__init__.py").exists():
            return str((potential_path / "__init__.py").relative_to(self.root_path))
        
        # Check for file
        if potential_path.with_suffix(".py").exists():
            return str(potential_path.with_suffix(".py").relative_to(self.root_path))
            
        return None
