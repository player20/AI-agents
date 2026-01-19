"""
Code Parser Module using Tree-sitter

Provides AST-level code parsing for multiple languages.
Enables agents to understand code structure, extract definitions,
and perform intelligent code analysis.

Features:
- Multi-language support (Python, TypeScript, JavaScript, Go, Rust, etc.)
- Function/class/method extraction
- Import/dependency analysis
- Code complexity metrics
- Symbol table generation
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Language(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    TSX = "tsx"
    JSX = "jsx"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
    CSHARP = "c_sharp"
    CPP = "cpp"
    C = "c"
    RUBY = "ruby"
    PHP = "php"
    SWIFT = "swift"
    KOTLIN = "kotlin"
    HTML = "html"
    CSS = "css"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"


@dataclass
class CodeLocation:
    """Location in source code"""
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    def to_dict(self) -> Dict[str, int]:
        return {
            "start_line": self.start_line,
            "start_column": self.start_column,
            "end_line": self.end_line,
            "end_column": self.end_column
        }


@dataclass
class Parameter:
    """Function/method parameter"""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None


@dataclass
class FunctionDef:
    """Function or method definition"""
    name: str
    location: CodeLocation
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    class_name: Optional[str] = None
    body_lines: int = 0
    complexity: int = 1  # Cyclomatic complexity


@dataclass
class ClassDef:
    """Class definition"""
    name: str
    location: CodeLocation
    base_classes: List[str] = field(default_factory=list)
    methods: List[FunctionDef] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    decorators: List[str] = field(default_factory=list)


@dataclass
class ImportDef:
    """Import statement"""
    module: str
    names: List[str] = field(default_factory=list)  # Specific imports
    alias: Optional[str] = None
    is_from_import: bool = False
    location: CodeLocation = None


@dataclass
class VariableDef:
    """Variable/constant definition"""
    name: str
    location: CodeLocation
    type_annotation: Optional[str] = None
    value: Optional[str] = None
    is_constant: bool = False


@dataclass
class ParseResult:
    """Complete parse result for a file"""
    language: Language
    imports: List[ImportDef] = field(default_factory=list)
    classes: List[ClassDef] = field(default_factory=list)
    functions: List[FunctionDef] = field(default_factory=list)
    variables: List[VariableDef] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Metrics
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    complexity: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language.value,
            "imports": [{"module": i.module, "names": i.names} for i in self.imports],
            "classes": [
                {
                    "name": c.name,
                    "base_classes": c.base_classes,
                    "methods": [m.name for m in c.methods],
                    "location": c.location.to_dict()
                }
                for c in self.classes
            ],
            "functions": [
                {
                    "name": f.name,
                    "parameters": [p.name for p in f.parameters],
                    "return_type": f.return_type,
                    "is_async": f.is_async,
                    "complexity": f.complexity,
                    "location": f.location.to_dict()
                }
                for f in self.functions
            ],
            "variables": [{"name": v.name, "type": v.type_annotation} for v in self.variables],
            "exports": self.exports,
            "metrics": {
                "total_lines": self.total_lines,
                "code_lines": self.code_lines,
                "comment_lines": self.comment_lines,
                "blank_lines": self.blank_lines,
                "complexity": self.complexity
            },
            "errors": self.errors
        }


class CodeParser:
    """
    Multi-language code parser using Tree-sitter.

    Example:
        parser = CodeParser()

        result = parser.parse('''
        def hello(name: str) -> str:
            \"\"\"Say hello\"\"\"
            return f"Hello, {name}!"
        ''', Language.PYTHON)

        print(result.functions[0].name)  # "hello"
        print(result.functions[0].return_type)  # "str"
    """

    def __init__(self):
        self._parsers: Dict[Language, Any] = {}
        self._tree_sitter_available = False
        self._init_tree_sitter()

    def _init_tree_sitter(self):
        """Initialize tree-sitter parsers"""
        try:
            import tree_sitter_python
            import tree_sitter_javascript
            import tree_sitter_typescript
            from tree_sitter import Language as TSLanguage, Parser

            self._tree_sitter_available = True

            # Initialize parsers for each language
            language_modules = {
                Language.PYTHON: tree_sitter_python,
                Language.JAVASCRIPT: tree_sitter_javascript,
                Language.JSX: tree_sitter_javascript,
            }

            # Try to import TypeScript languages
            try:
                self._parsers[Language.TYPESCRIPT] = self._create_parser(
                    tree_sitter_typescript.language_typescript()
                )
                self._parsers[Language.TSX] = self._create_parser(
                    tree_sitter_typescript.language_tsx()
                )
            except Exception:
                pass

            for lang, module in language_modules.items():
                try:
                    self._parsers[lang] = self._create_parser(module.language())
                except Exception as e:
                    logger.debug(f"Could not load {lang}: {e}")

            logger.info(f"Tree-sitter initialized with languages: {list(self._parsers.keys())}")

        except ImportError as e:
            logger.warning(f"Tree-sitter not available: {e}. Using fallback parser.")
            self._tree_sitter_available = False

    def _create_parser(self, language) -> Any:
        """Create a parser for a specific language"""
        from tree_sitter import Parser
        parser = Parser()
        parser.language = language
        return parser

    def parse(self, code: str, language: Language) -> ParseResult:
        """
        Parse source code and extract structure.

        Args:
            code: Source code string
            language: Programming language

        Returns:
            ParseResult with extracted definitions
        """
        if self._tree_sitter_available and language in self._parsers:
            return self._parse_with_tree_sitter(code, language)
        else:
            return self._parse_fallback(code, language)

    def parse_file(self, file_path: str) -> ParseResult:
        """Parse a file, auto-detecting language from extension"""
        path = Path(file_path)
        language = self._detect_language(path)

        with open(path, 'r', encoding='utf-8') as f:
            code = f.read()

        result = self.parse(code, language)
        return result

    def _detect_language(self, path: Path) -> Language:
        """Detect language from file extension"""
        ext_map = {
            '.py': Language.PYTHON,
            '.js': Language.JAVASCRIPT,
            '.jsx': Language.JSX,
            '.ts': Language.TYPESCRIPT,
            '.tsx': Language.TSX,
            '.go': Language.GO,
            '.rs': Language.RUST,
            '.java': Language.JAVA,
            '.cs': Language.CSHARP,
            '.cpp': Language.CPP,
            '.c': Language.C,
            '.rb': Language.RUBY,
            '.php': Language.PHP,
            '.swift': Language.SWIFT,
            '.kt': Language.KOTLIN,
            '.html': Language.HTML,
            '.css': Language.CSS,
            '.json': Language.JSON,
            '.yaml': Language.YAML,
            '.yml': Language.YAML,
            '.md': Language.MARKDOWN,
        }
        return ext_map.get(path.suffix.lower(), Language.PYTHON)

    def _parse_with_tree_sitter(self, code: str, language: Language) -> ParseResult:
        """Parse using tree-sitter AST"""
        parser = self._parsers[language]
        tree = parser.parse(bytes(code, 'utf-8'))

        result = ParseResult(language=language)
        result.total_lines = code.count('\n') + 1

        # Count line types
        for line in code.split('\n'):
            stripped = line.strip()
            if not stripped:
                result.blank_lines += 1
            elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                result.comment_lines += 1
            else:
                result.code_lines += 1

        # Extract definitions based on language
        if language == Language.PYTHON:
            self._extract_python_definitions(tree.root_node, code, result)
        elif language in (Language.JAVASCRIPT, Language.JSX):
            self._extract_js_definitions(tree.root_node, code, result)
        elif language in (Language.TYPESCRIPT, Language.TSX):
            self._extract_ts_definitions(tree.root_node, code, result)

        # Calculate total complexity
        result.complexity = sum(f.complexity for f in result.functions)
        for cls in result.classes:
            result.complexity += sum(m.complexity for m in cls.methods)

        return result

    def _extract_python_definitions(self, node, code: str, result: ParseResult):
        """Extract definitions from Python AST"""
        cursor = node.walk()

        def visit(cursor, class_name: Optional[str] = None):
            node = cursor.node

            if node.type == 'import_statement':
                result.imports.append(self._parse_python_import(node, code))

            elif node.type == 'import_from_statement':
                result.imports.append(self._parse_python_from_import(node, code))

            elif node.type == 'class_definition':
                class_def = self._parse_python_class(node, code)
                result.classes.append(class_def)
                # Visit class body for methods
                if cursor.goto_first_child():
                    while True:
                        visit(cursor, class_def.name)
                        if not cursor.goto_next_sibling():
                            break
                    cursor.goto_parent()
                return  # Don't recurse further

            elif node.type == 'function_definition':
                func_def = self._parse_python_function(node, code, class_name)
                if class_name:
                    # Find the class and add method
                    for cls in result.classes:
                        if cls.name == class_name:
                            cls.methods.append(func_def)
                            break
                else:
                    result.functions.append(func_def)

            elif node.type == 'assignment':
                var_def = self._parse_python_variable(node, code)
                if var_def:
                    result.variables.append(var_def)

            # Recurse into children
            if cursor.goto_first_child():
                while True:
                    visit(cursor, class_name)
                    if not cursor.goto_next_sibling():
                        break
                cursor.goto_parent()

        visit(cursor)

    def _parse_python_import(self, node, code: str) -> ImportDef:
        """Parse Python import statement"""
        text = self._get_node_text(node, code)
        # Simple parsing: import module as alias
        parts = text.replace('import ', '').split(' as ')
        module = parts[0].strip()
        alias = parts[1].strip() if len(parts) > 1 else None

        return ImportDef(
            module=module,
            alias=alias,
            location=self._get_location(node)
        )

    def _parse_python_from_import(self, node, code: str) -> ImportDef:
        """Parse Python from...import statement"""
        text = self._get_node_text(node, code)
        # from module import name1, name2
        parts = text.split(' import ')
        module = parts[0].replace('from ', '').strip()
        names = [n.strip() for n in parts[1].split(',')] if len(parts) > 1 else []

        return ImportDef(
            module=module,
            names=names,
            is_from_import=True,
            location=self._get_location(node)
        )

    def _parse_python_class(self, node, code: str) -> ClassDef:
        """Parse Python class definition"""
        name = ""
        bases = []
        docstring = None
        decorators = []

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, code)
            elif child.type == 'argument_list':
                # Base classes
                for arg in child.children:
                    if arg.type == 'identifier':
                        bases.append(self._get_node_text(arg, code))
            elif child.type == 'block':
                # Check for docstring
                for stmt in child.children:
                    if stmt.type == 'expression_statement':
                        expr = stmt.children[0] if stmt.children else None
                        if expr and expr.type == 'string':
                            docstring = self._get_node_text(expr, code).strip('\"\'')
                        break
            elif child.type == 'decorator':
                decorators.append(self._get_node_text(child, code).lstrip('@'))

        return ClassDef(
            name=name,
            location=self._get_location(node),
            base_classes=bases,
            docstring=docstring,
            decorators=decorators
        )

    def _parse_python_function(self, node, code: str, class_name: Optional[str] = None) -> FunctionDef:
        """Parse Python function definition"""
        name = ""
        params = []
        return_type = None
        docstring = None
        decorators = []
        is_async = False

        # Check parent for async
        if node.parent and node.parent.type == 'decorated_definition':
            for child in node.parent.children:
                if child.type == 'decorator':
                    decorators.append(self._get_node_text(child, code).lstrip('@'))

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, code)
            elif child.type == 'parameters':
                params = self._parse_python_parameters(child, code)
            elif child.type == 'type':
                return_type = self._get_node_text(child, code)
            elif child.type == 'block':
                # Docstring and complexity
                for stmt in child.children:
                    if stmt.type == 'expression_statement':
                        expr = stmt.children[0] if stmt.children else None
                        if expr and expr.type == 'string' and not docstring:
                            docstring = self._get_node_text(expr, code).strip('\"\'')

        # Calculate complexity
        complexity = self._calculate_complexity(node, code)

        # Count body lines
        body_lines = node.end_point[0] - node.start_point[0]

        return FunctionDef(
            name=name,
            location=self._get_location(node),
            parameters=params,
            return_type=return_type,
            docstring=docstring,
            decorators=decorators,
            is_async='async' in self._get_node_text(node, code)[:20],
            is_method=class_name is not None,
            class_name=class_name,
            body_lines=body_lines,
            complexity=complexity
        )

    def _parse_python_parameters(self, node, code: str) -> List[Parameter]:
        """Parse Python function parameters"""
        params = []
        for child in node.children:
            if child.type in ('identifier', 'typed_parameter', 'default_parameter'):
                param_name = ""
                param_type = None
                default = None

                if child.type == 'identifier':
                    param_name = self._get_node_text(child, code)
                elif child.type == 'typed_parameter':
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            param_name = self._get_node_text(subchild, code)
                        elif subchild.type == 'type':
                            param_type = self._get_node_text(subchild, code)
                elif child.type == 'default_parameter':
                    for subchild in child.children:
                        if subchild.type == 'identifier':
                            param_name = self._get_node_text(subchild, code)
                        # Could extract default value here

                if param_name and param_name not in ('self', 'cls'):
                    params.append(Parameter(
                        name=param_name,
                        type_annotation=param_type,
                        default_value=default
                    ))
        return params

    def _parse_python_variable(self, node, code: str) -> Optional[VariableDef]:
        """Parse Python variable assignment"""
        name = ""
        type_ann = None

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, code)
                break
            elif child.type == 'pattern_list':
                # Multiple assignment, skip for now
                return None

        if not name:
            return None

        # Check if constant (ALL_CAPS)
        is_constant = name.isupper()

        return VariableDef(
            name=name,
            location=self._get_location(node),
            type_annotation=type_ann,
            is_constant=is_constant
        )

    def _extract_js_definitions(self, node, code: str, result: ParseResult):
        """Extract definitions from JavaScript AST"""
        self._extract_js_ts_definitions(node, code, result, is_typescript=False)

    def _extract_ts_definitions(self, node, code: str, result: ParseResult):
        """Extract definitions from TypeScript AST"""
        self._extract_js_ts_definitions(node, code, result, is_typescript=True)

    def _extract_js_ts_definitions(self, node, code: str, result: ParseResult, is_typescript: bool):
        """Extract definitions from JS/TS AST"""
        cursor = node.walk()

        def visit(cursor, class_name: Optional[str] = None):
            node = cursor.node

            if node.type == 'import_statement':
                imp = self._parse_js_import(node, code)
                if imp:
                    result.imports.append(imp)

            elif node.type == 'export_statement':
                # Track exports
                text = self._get_node_text(node, code)
                if 'export default' in text:
                    result.exports.append('default')
                elif 'export' in text:
                    # Extract export names
                    for child in node.children:
                        if child.type == 'identifier':
                            result.exports.append(self._get_node_text(child, code))

            elif node.type == 'class_declaration':
                class_def = self._parse_js_class(node, code)
                result.classes.append(class_def)
                return

            elif node.type in ('function_declaration', 'arrow_function', 'method_definition'):
                func_def = self._parse_js_function(node, code, class_name)
                if func_def:
                    if class_name:
                        for cls in result.classes:
                            if cls.name == class_name:
                                cls.methods.append(func_def)
                                break
                    else:
                        result.functions.append(func_def)

            elif node.type in ('variable_declaration', 'lexical_declaration'):
                for child in node.children:
                    if child.type == 'variable_declarator':
                        var_def = self._parse_js_variable(child, code)
                        if var_def:
                            result.variables.append(var_def)

            # Recurse
            if cursor.goto_first_child():
                while True:
                    visit(cursor, class_name)
                    if not cursor.goto_next_sibling():
                        break
                cursor.goto_parent()

        visit(cursor)

    def _parse_js_import(self, node, code: str) -> Optional[ImportDef]:
        """Parse JavaScript/TypeScript import"""
        text = self._get_node_text(node, code)

        # Basic parsing for common patterns
        # import X from 'module'
        # import { X, Y } from 'module'
        # import * as X from 'module'

        names = []
        module = ""
        alias = None

        for child in node.children:
            if child.type == 'string':
                module = self._get_node_text(child, code).strip('\'"')
            elif child.type == 'identifier':
                names.append(self._get_node_text(child, code))
            elif child.type == 'import_clause':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        names.append(self._get_node_text(subchild, code))
                    elif subchild.type == 'named_imports':
                        for imp in subchild.children:
                            if imp.type == 'import_specifier':
                                for spec in imp.children:
                                    if spec.type == 'identifier':
                                        names.append(self._get_node_text(spec, code))

        if module:
            return ImportDef(
                module=module,
                names=names,
                alias=alias,
                location=self._get_location(node)
            )
        return None

    def _parse_js_class(self, node, code: str) -> ClassDef:
        """Parse JavaScript/TypeScript class"""
        name = ""
        bases = []

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, code)
            elif child.type == 'class_heritage':
                for subchild in child.children:
                    if subchild.type == 'identifier':
                        bases.append(self._get_node_text(subchild, code))

        return ClassDef(
            name=name,
            location=self._get_location(node),
            base_classes=bases
        )

    def _parse_js_function(self, node, code: str, class_name: Optional[str] = None) -> Optional[FunctionDef]:
        """Parse JavaScript/TypeScript function"""
        name = ""
        is_async = False

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, code)
            elif child.type == 'property_identifier':
                name = self._get_node_text(child, code)

        # Check for async
        text = self._get_node_text(node, code)
        is_async = text.strip().startswith('async')

        if not name and node.type == 'arrow_function':
            # Anonymous arrow function, check parent
            return None

        return FunctionDef(
            name=name,
            location=self._get_location(node),
            is_async=is_async,
            is_method=class_name is not None,
            class_name=class_name,
            complexity=self._calculate_complexity(node, code)
        )

    def _parse_js_variable(self, node, code: str) -> Optional[VariableDef]:
        """Parse JavaScript variable"""
        name = ""

        for child in node.children:
            if child.type == 'identifier':
                name = self._get_node_text(child, code)
                break

        if not name:
            return None

        return VariableDef(
            name=name,
            location=self._get_location(node),
            is_constant=name.isupper()
        )

    def _get_node_text(self, node, code: str) -> str:
        """Get text content of a node"""
        return code[node.start_byte:node.end_byte]

    def _get_location(self, node) -> CodeLocation:
        """Get location from node"""
        return CodeLocation(
            start_line=node.start_point[0] + 1,
            start_column=node.start_point[1],
            end_line=node.end_point[0] + 1,
            end_column=node.end_point[1]
        )

    def _calculate_complexity(self, node, code: str) -> int:
        """Calculate cyclomatic complexity"""
        text = self._get_node_text(node, code)

        # Count decision points
        complexity = 1  # Base complexity

        # Control flow keywords
        keywords = ['if', 'elif', 'else if', 'for', 'while', 'case',
                   'catch', 'except', '&&', '||', 'and', 'or', '?']

        for keyword in keywords:
            complexity += text.count(f' {keyword} ') + text.count(f'\n{keyword} ')

        return complexity

    def _parse_fallback(self, code: str, language: Language) -> ParseResult:
        """Fallback parser using regex when tree-sitter unavailable"""
        import re

        result = ParseResult(language=language)
        lines = code.split('\n')
        result.total_lines = len(lines)

        # Count line types
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result.blank_lines += 1
            elif stripped.startswith('#') or stripped.startswith('//'):
                result.comment_lines += 1
            else:
                result.code_lines += 1

        if language == Language.PYTHON:
            # Python patterns
            class_pattern = r'^class\s+(\w+)(?:\(([^)]*)\))?:'
            func_pattern = r'^(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*(\S+))?:'
            import_pattern = r'^(?:from\s+(\S+)\s+)?import\s+(.+)$'

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Classes
                match = re.match(class_pattern, stripped)
                if match:
                    result.classes.append(ClassDef(
                        name=match.group(1),
                        location=CodeLocation(i+1, 0, i+1, len(line)),
                        base_classes=match.group(2).split(',') if match.group(2) else []
                    ))

                # Functions
                match = re.match(func_pattern, stripped)
                if match:
                    result.functions.append(FunctionDef(
                        name=match.group(1),
                        location=CodeLocation(i+1, 0, i+1, len(line)),
                        return_type=match.group(3),
                        is_async='async' in stripped
                    ))

                # Imports
                match = re.match(import_pattern, stripped)
                if match:
                    result.imports.append(ImportDef(
                        module=match.group(1) or match.group(2).split()[0],
                        names=match.group(2).split(',') if match.group(1) else [],
                        is_from_import=bool(match.group(1)),
                        location=CodeLocation(i+1, 0, i+1, len(line))
                    ))

        elif language in (Language.JAVASCRIPT, Language.TYPESCRIPT, Language.TSX, Language.JSX):
            # JS/TS patterns
            class_pattern = r'^(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?'
            func_pattern = r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)'
            arrow_pattern = r'^(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
            import_pattern = r"^import\s+(?:{([^}]+)}|(\w+))\s+from\s+['\"]([^'\"]+)['\"]"

            for i, line in enumerate(lines):
                stripped = line.strip()

                # Classes
                match = re.match(class_pattern, stripped)
                if match:
                    result.classes.append(ClassDef(
                        name=match.group(1),
                        location=CodeLocation(i+1, 0, i+1, len(line)),
                        base_classes=[match.group(2)] if match.group(2) else []
                    ))

                # Functions
                match = re.match(func_pattern, stripped)
                if match:
                    result.functions.append(FunctionDef(
                        name=match.group(1),
                        location=CodeLocation(i+1, 0, i+1, len(line)),
                        is_async='async' in stripped
                    ))

                # Arrow functions
                match = re.match(arrow_pattern, stripped)
                if match:
                    result.functions.append(FunctionDef(
                        name=match.group(1),
                        location=CodeLocation(i+1, 0, i+1, len(line)),
                        is_async='async' in stripped
                    ))

                # Imports
                match = re.match(import_pattern, stripped)
                if match:
                    names = []
                    if match.group(1):
                        names = [n.strip() for n in match.group(1).split(',')]
                    elif match.group(2):
                        names = [match.group(2)]

                    result.imports.append(ImportDef(
                        module=match.group(3),
                        names=names,
                        location=CodeLocation(i+1, 0, i+1, len(line))
                    ))

        return result


# ===========================================
# Convenience Functions
# ===========================================

_default_parser: Optional[CodeParser] = None


def get_parser() -> CodeParser:
    """Get the default code parser"""
    global _default_parser
    if _default_parser is None:
        _default_parser = CodeParser()
    return _default_parser


def parse_code(code: str, language: str) -> ParseResult:
    """Parse code and extract structure"""
    parser = get_parser()
    lang = Language(language.lower()) if language.lower() in [l.value for l in Language] else Language.PYTHON
    return parser.parse(code, lang)


def parse_file(file_path: str) -> ParseResult:
    """Parse a file and extract structure"""
    parser = get_parser()
    return parser.parse_file(file_path)


def extract_functions(code: str, language: str) -> List[Dict[str, Any]]:
    """Extract all functions from code"""
    result = parse_code(code, language)
    return [
        {
            "name": f.name,
            "parameters": [p.name for p in f.parameters],
            "return_type": f.return_type,
            "is_async": f.is_async,
            "line": f.location.start_line,
            "complexity": f.complexity
        }
        for f in result.functions
    ]


def extract_classes(code: str, language: str) -> List[Dict[str, Any]]:
    """Extract all classes from code"""
    result = parse_code(code, language)
    return [
        {
            "name": c.name,
            "base_classes": c.base_classes,
            "methods": [m.name for m in c.methods],
            "line": c.location.start_line
        }
        for c in result.classes
    ]


def get_code_metrics(code: str, language: str) -> Dict[str, Any]:
    """Get code metrics"""
    result = parse_code(code, language)
    return {
        "total_lines": result.total_lines,
        "code_lines": result.code_lines,
        "comment_lines": result.comment_lines,
        "blank_lines": result.blank_lines,
        "complexity": result.complexity,
        "num_functions": len(result.functions),
        "num_classes": len(result.classes),
        "num_imports": len(result.imports)
    }
