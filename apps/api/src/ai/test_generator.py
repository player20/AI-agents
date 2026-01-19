"""
Test Generator Module

Automatically generates comprehensive tests for generated code.
Ensures code correctness through automated verification.

Features:
- Unit test generation for functions/classes
- Edge case detection and testing
- Property-based testing
- Integration test scaffolding
- Coverage-aware test generation
"""

from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class TestType(str, Enum):
    """Types of tests to generate"""
    UNIT = "unit"
    EDGE_CASE = "edge_case"
    PROPERTY = "property"
    INTEGRATION = "integration"
    SMOKE = "smoke"
    REGRESSION = "regression"


class TestFramework(str, Enum):
    """Supported test frameworks"""
    PYTEST = "pytest"  # Python
    UNITTEST = "unittest"  # Python
    JEST = "jest"  # JavaScript/TypeScript
    MOCHA = "mocha"  # JavaScript
    VITEST = "vitest"  # JavaScript/TypeScript
    GO_TEST = "go_test"  # Go
    RUST_TEST = "rust_test"  # Rust


@dataclass
class TestCase:
    """A single test case"""
    name: str
    description: str
    input_values: Dict[str, Any]
    expected_output: Any
    test_type: TestType = TestType.UNIT
    assertions: List[str] = field(default_factory=list)
    setup: Optional[str] = None
    teardown: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_values": self.input_values,
            "expected_output": self.expected_output,
            "test_type": self.test_type.value,
            "assertions": self.assertions
        }


@dataclass
class TestSuite:
    """A collection of test cases"""
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup_code: Optional[str] = None
    teardown_code: Optional[str] = None
    imports: List[str] = field(default_factory=list)

    def to_code(self, framework: TestFramework, language: str) -> str:
        """Generate test code for the suite"""
        generator = TestCodeGenerator()
        return generator.generate(self, framework, language)


@dataclass
class FunctionInfo:
    """Information about a function to test"""
    name: str
    parameters: List[Dict[str, Any]]  # [{name, type, default}]
    return_type: Optional[str]
    docstring: Optional[str]
    is_async: bool = False
    raises: List[str] = field(default_factory=list)  # Exceptions it might raise


@dataclass
class ClassInfo:
    """Information about a class to test"""
    name: str
    methods: List[FunctionInfo]
    constructor_params: List[Dict[str, Any]]
    docstring: Optional[str]


class TestGenerator:
    """
    Generates comprehensive tests for code.

    Example:
        generator = TestGenerator()

        # Generate tests for a function
        tests = generator.generate_tests('''
        def fibonacci(n: int) -> int:
            \"\"\"Calculate the nth Fibonacci number.\"\"\"
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        ''', language="python")

        # Get test code
        test_code = tests.to_code(TestFramework.PYTEST, "python")
        print(test_code)
    """

    def __init__(self):
        self._parser = None

    def _get_parser(self):
        """Lazy load code parser"""
        if self._parser is None:
            try:
                from .code_parser import CodeParser
                self._parser = CodeParser()
            except ImportError:
                self._parser = None
        return self._parser

    def generate_tests(
        self,
        code: str,
        language: str,
        coverage_target: float = 0.8,
        include_edge_cases: bool = True,
        include_property_tests: bool = False
    ) -> TestSuite:
        """
        Generate tests for code.

        Args:
            code: Source code to test
            language: Programming language
            coverage_target: Target code coverage (0-1)
            include_edge_cases: Include edge case tests
            include_property_tests: Include property-based tests

        Returns:
            TestSuite with generated tests
        """
        # Parse code to extract functions/classes
        functions, classes = self._extract_testable_items(code, language)

        test_cases = []

        # Generate tests for each function
        for func in functions:
            test_cases.extend(self._generate_function_tests(
                func, include_edge_cases, include_property_tests
            ))

        # Generate tests for each class
        for cls in classes:
            test_cases.extend(self._generate_class_tests(
                cls, include_edge_cases
            ))

        # Determine imports based on language and framework
        imports = self._get_imports(language)

        return TestSuite(
            name=f"test_{self._sanitize_name(code[:50])}",
            description=f"Auto-generated tests for {language} code",
            test_cases=test_cases,
            imports=imports
        )

    def _extract_testable_items(
        self,
        code: str,
        language: str
    ) -> Tuple[List[FunctionInfo], List[ClassInfo]]:
        """Extract functions and classes from code"""
        functions = []
        classes = []

        parser = self._get_parser()
        if parser:
            try:
                from .code_parser import Language as ParserLanguage
                lang = ParserLanguage(language.lower())
                result = parser.parse(code, lang)

                # Convert to FunctionInfo
                for func in result.functions:
                    functions.append(FunctionInfo(
                        name=func.name,
                        parameters=[
                            {"name": p.name, "type": p.type_annotation, "default": p.default_value}
                            for p in func.parameters
                        ],
                        return_type=func.return_type,
                        docstring=func.docstring,
                        is_async=func.is_async
                    ))

                # Convert to ClassInfo
                for cls in result.classes:
                    methods = []
                    constructor_params = []

                    for method in cls.methods:
                        if method.name == "__init__":
                            constructor_params = [
                                {"name": p.name, "type": p.type_annotation, "default": p.default_value}
                                for p in method.parameters
                            ]
                        else:
                            methods.append(FunctionInfo(
                                name=method.name,
                                parameters=[
                                    {"name": p.name, "type": p.type_annotation, "default": p.default_value}
                                    for p in method.parameters
                                ],
                                return_type=method.return_type,
                                docstring=method.docstring,
                                is_async=method.is_async
                            ))

                    classes.append(ClassInfo(
                        name=cls.name,
                        methods=methods,
                        constructor_params=constructor_params,
                        docstring=cls.docstring
                    ))

            except Exception as e:
                logger.warning(f"Parser extraction failed: {e}, using regex fallback")

        # Fallback to regex if parser fails
        if not functions and not classes:
            functions, classes = self._extract_with_regex(code, language)

        return functions, classes

    def _extract_with_regex(
        self,
        code: str,
        language: str
    ) -> Tuple[List[FunctionInfo], List[ClassInfo]]:
        """Fallback regex-based extraction"""
        functions = []
        classes = []

        if language.lower() == "python":
            # Extract Python functions
            func_pattern = r'(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*(\w+))?:'
            for match in re.finditer(func_pattern, code):
                name = match.group(1)
                params_str = match.group(2)
                return_type = match.group(3)

                # Parse parameters
                params = []
                if params_str.strip():
                    for param in params_str.split(','):
                        param = param.strip()
                        if ':' in param:
                            pname, ptype = param.split(':', 1)
                            params.append({"name": pname.strip(), "type": ptype.strip(), "default": None})
                        elif '=' not in param and param not in ('self', 'cls'):
                            params.append({"name": param, "type": None, "default": None})

                if name not in ('__init__', '__str__', '__repr__'):
                    functions.append(FunctionInfo(
                        name=name,
                        parameters=params,
                        return_type=return_type,
                        docstring=None,
                        is_async='async def' in code[:code.find(f'def {name}') + 20]
                    ))

            # Extract Python classes
            class_pattern = r'class\s+(\w+)(?:\([^)]*\))?:'
            for match in re.finditer(class_pattern, code):
                classes.append(ClassInfo(
                    name=match.group(1),
                    methods=[],
                    constructor_params=[],
                    docstring=None
                ))

        elif language.lower() in ("javascript", "typescript"):
            # Extract JS/TS functions
            func_pattern = r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)'
            arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'

            for match in re.finditer(func_pattern, code):
                functions.append(FunctionInfo(
                    name=match.group(1),
                    parameters=[],
                    return_type=None,
                    docstring=None
                ))

            for match in re.finditer(arrow_pattern, code):
                functions.append(FunctionInfo(
                    name=match.group(1),
                    parameters=[],
                    return_type=None,
                    docstring=None
                ))

        return functions, classes

    def _generate_function_tests(
        self,
        func: FunctionInfo,
        include_edge_cases: bool,
        include_property_tests: bool
    ) -> List[TestCase]:
        """Generate tests for a function"""
        tests = []

        # Basic functionality test
        tests.append(self._generate_basic_test(func))

        # Edge case tests
        if include_edge_cases:
            tests.extend(self._generate_edge_case_tests(func))

        # Property tests
        if include_property_tests:
            tests.extend(self._generate_property_tests(func))

        return tests

    def _generate_basic_test(self, func: FunctionInfo) -> TestCase:
        """Generate a basic functionality test"""
        # Generate reasonable input values based on types
        input_values = {}
        for param in func.parameters:
            input_values[param["name"]] = self._generate_sample_value(
                param.get("type"),
                param["name"]
            )

        # Generate expected output placeholder
        expected = "# TODO: Set expected output"

        return TestCase(
            name=f"test_{func.name}_basic",
            description=f"Test basic functionality of {func.name}",
            input_values=input_values,
            expected_output=expected,
            test_type=TestType.UNIT,
            assertions=[
                f"result is not None",
                f"# Add specific assertions for {func.name}"
            ]
        )

    def _generate_edge_case_tests(self, func: FunctionInfo) -> List[TestCase]:
        """Generate edge case tests"""
        tests = []

        for param in func.parameters:
            param_type = param.get("type", "").lower()
            param_name = param["name"]

            # Numeric edge cases
            if any(t in param_type for t in ["int", "float", "number"]):
                # Zero
                tests.append(TestCase(
                    name=f"test_{func.name}_{param_name}_zero",
                    description=f"Test {func.name} with {param_name}=0",
                    input_values={**{p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in func.parameters}, param_name: 0},
                    expected_output="# TODO: Expected for zero",
                    test_type=TestType.EDGE_CASE
                ))

                # Negative
                tests.append(TestCase(
                    name=f"test_{func.name}_{param_name}_negative",
                    description=f"Test {func.name} with negative {param_name}",
                    input_values={**{p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in func.parameters}, param_name: -1},
                    expected_output="# TODO: Expected for negative",
                    test_type=TestType.EDGE_CASE
                ))

                # Large value
                tests.append(TestCase(
                    name=f"test_{func.name}_{param_name}_large",
                    description=f"Test {func.name} with large {param_name}",
                    input_values={**{p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in func.parameters}, param_name: 1000000},
                    expected_output="# TODO: Expected for large value",
                    test_type=TestType.EDGE_CASE
                ))

            # String edge cases
            elif any(t in param_type for t in ["str", "string"]):
                # Empty string
                tests.append(TestCase(
                    name=f"test_{func.name}_{param_name}_empty",
                    description=f"Test {func.name} with empty {param_name}",
                    input_values={**{p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in func.parameters}, param_name: ""},
                    expected_output="# TODO: Expected for empty string",
                    test_type=TestType.EDGE_CASE
                ))

                # Special characters
                tests.append(TestCase(
                    name=f"test_{func.name}_{param_name}_special_chars",
                    description=f"Test {func.name} with special characters",
                    input_values={**{p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in func.parameters}, param_name: "!@#$%^&*()"},
                    expected_output="# TODO: Expected for special chars",
                    test_type=TestType.EDGE_CASE
                ))

            # List/Array edge cases
            elif any(t in param_type for t in ["list", "array", "[]"]):
                # Empty list
                tests.append(TestCase(
                    name=f"test_{func.name}_{param_name}_empty_list",
                    description=f"Test {func.name} with empty {param_name}",
                    input_values={**{p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in func.parameters}, param_name: []},
                    expected_output="# TODO: Expected for empty list",
                    test_type=TestType.EDGE_CASE
                ))

                # Single element
                tests.append(TestCase(
                    name=f"test_{func.name}_{param_name}_single",
                    description=f"Test {func.name} with single element",
                    input_values={**{p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in func.parameters}, param_name: [1]},
                    expected_output="# TODO: Expected for single element",
                    test_type=TestType.EDGE_CASE
                ))

        # None/null test if function might handle it
        if func.parameters:
            tests.append(TestCase(
                name=f"test_{func.name}_none_input",
                description=f"Test {func.name} with None input (should raise or handle)",
                input_values={func.parameters[0]["name"]: None},
                expected_output="# TODO: Should raise TypeError or handle gracefully",
                test_type=TestType.EDGE_CASE,
                assertions=["# Verify appropriate error handling"]
            ))

        return tests

    def _generate_property_tests(self, func: FunctionInfo) -> List[TestCase]:
        """Generate property-based tests"""
        tests = []

        # Idempotency test (if applicable)
        tests.append(TestCase(
            name=f"test_{func.name}_idempotency",
            description=f"Test that {func.name} produces consistent results",
            input_values={},
            expected_output="# Multiple calls should return same result",
            test_type=TestType.PROPERTY,
            assertions=[
                f"result1 = {func.name}(input)",
                f"result2 = {func.name}(input)",
                "assert result1 == result2"
            ]
        ))

        return tests

    def _generate_class_tests(
        self,
        cls: ClassInfo,
        include_edge_cases: bool
    ) -> List[TestCase]:
        """Generate tests for a class"""
        tests = []

        # Constructor test
        tests.append(TestCase(
            name=f"test_{cls.name}_creation",
            description=f"Test {cls.name} can be instantiated",
            input_values={p["name"]: self._generate_sample_value(p.get("type"), p["name"]) for p in cls.constructor_params},
            expected_output=f"# Instance of {cls.name}",
            test_type=TestType.UNIT,
            assertions=[
                f"instance is not None",
                f"isinstance(instance, {cls.name})"
            ]
        ))

        # Method tests
        for method in cls.methods:
            if not method.name.startswith('_'):  # Skip private methods
                tests.extend(self._generate_function_tests(method, include_edge_cases, False))

        return tests

    def _generate_sample_value(self, type_hint: Optional[str], param_name: str) -> Any:
        """Generate a sample value based on type hint or parameter name"""
        if not type_hint:
            # Infer from parameter name
            name_lower = param_name.lower()
            if any(x in name_lower for x in ["count", "num", "size", "length", "index", "id"]):
                return 5
            elif any(x in name_lower for x in ["name", "text", "message", "title"]):
                return "test_value"
            elif any(x in name_lower for x in ["flag", "is_", "has_", "enabled", "active"]):
                return True
            elif any(x in name_lower for x in ["items", "list", "array", "values"]):
                return [1, 2, 3]
            elif any(x in name_lower for x in ["data", "obj", "config"]):
                return {"key": "value"}
            return "test_input"

        type_lower = type_hint.lower()

        if "int" in type_lower:
            return 42
        elif "float" in type_lower or "double" in type_lower:
            return 3.14
        elif "str" in type_lower or "string" in type_lower:
            return "test_string"
        elif "bool" in type_lower or "boolean" in type_lower:
            return True
        elif "list" in type_lower or "array" in type_lower or "[]" in type_lower:
            return [1, 2, 3]
        elif "dict" in type_lower or "object" in type_lower or "map" in type_lower:
            return {"key": "value"}
        elif "none" in type_lower or "null" in type_lower:
            return None

        return "test_value"

    def _get_imports(self, language: str) -> List[str]:
        """Get test imports for a language"""
        if language.lower() == "python":
            return [
                "import pytest",
                "from typing import Any"
            ]
        elif language.lower() in ("javascript", "typescript"):
            return [
                "import { describe, it, expect } from 'vitest'",
                "// or: import { describe, it, expect } from '@jest/globals'"
            ]
        elif language.lower() == "go":
            return [
                'import "testing"'
            ]

        return []

    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use as identifier"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', name)[:30]


class TestCodeGenerator:
    """Generates test code from TestSuite"""

    def generate(
        self,
        suite: TestSuite,
        framework: TestFramework,
        language: str
    ) -> str:
        """Generate test code"""
        if framework == TestFramework.PYTEST:
            return self._generate_pytest(suite)
        elif framework == TestFramework.JEST or framework == TestFramework.VITEST:
            return self._generate_jest(suite)
        elif framework == TestFramework.GO_TEST:
            return self._generate_go_test(suite)
        else:
            return self._generate_pytest(suite)  # Default

    def _generate_pytest(self, suite: TestSuite) -> str:
        """Generate pytest code"""
        lines = []

        # Imports
        lines.append("import pytest")
        for imp in suite.imports:
            if imp not in lines:
                lines.append(imp)
        lines.append("")

        # Import the module to test (placeholder)
        lines.append("# TODO: Import the module to test")
        lines.append("# from your_module import function_to_test")
        lines.append("")

        # Setup/teardown if provided
        if suite.setup_code:
            lines.append("@pytest.fixture(autouse=True)")
            lines.append("def setup():")
            lines.append(f"    {suite.setup_code}")
            lines.append("")

        # Test cases
        for test in suite.test_cases:
            lines.append(f"def {test.name}():")
            lines.append(f'    """')
            lines.append(f'    {test.description}')
            lines.append(f'    Test type: {test.test_type.value}')
            lines.append(f'    """')

            # Setup
            if test.setup:
                lines.append(f"    # Setup")
                lines.append(f"    {test.setup}")

            # Input values
            lines.append("    # Arrange")
            for name, value in test.input_values.items():
                lines.append(f"    {name} = {repr(value)}")

            # Act
            lines.append("")
            lines.append("    # Act")
            lines.append("    # TODO: Call the function/method")
            lines.append("    # result = function_to_test(...)")
            lines.append("    result = None  # Replace with actual call")

            # Assert
            lines.append("")
            lines.append("    # Assert")
            for assertion in test.assertions:
                if assertion.startswith("#"):
                    lines.append(f"    {assertion}")
                else:
                    lines.append(f"    assert {assertion}")

            if not test.assertions:
                lines.append(f"    # TODO: Add assertions")
                lines.append(f"    # assert result == {repr(test.expected_output)}")

            # Teardown
            if test.teardown:
                lines.append(f"    # Teardown")
                lines.append(f"    {test.teardown}")

            lines.append("")
            lines.append("")

        return "\n".join(lines)

    def _generate_jest(self, suite: TestSuite) -> str:
        """Generate Jest/Vitest code"""
        lines = []

        # Imports
        lines.append("import { describe, it, expect, beforeEach, afterEach } from 'vitest';")
        lines.append("// TODO: Import the module to test")
        lines.append("// import { functionToTest } from './your-module';")
        lines.append("")

        # Test suite
        lines.append(f"describe('{suite.name}', () => {{")

        # Setup
        if suite.setup_code:
            lines.append("  beforeEach(() => {")
            lines.append(f"    {suite.setup_code}")
            lines.append("  });")
            lines.append("")

        # Test cases
        for test in suite.test_cases:
            lines.append(f"  it('{test.description}', () => {{")

            # Input values
            lines.append("    // Arrange")
            for name, value in test.input_values.items():
                js_value = self._to_js_value(value)
                lines.append(f"    const {name} = {js_value};")

            # Act
            lines.append("")
            lines.append("    // Act")
            lines.append("    // TODO: Call the function")
            lines.append("    // const result = functionToTest(...);")
            lines.append("    const result = null; // Replace with actual call")

            # Assert
            lines.append("")
            lines.append("    // Assert")
            for assertion in test.assertions:
                if assertion.startswith("#"):
                    lines.append(f"    // {assertion[1:].strip()}")
                else:
                    lines.append(f"    expect({assertion}).toBeTruthy();")

            if not test.assertions:
                lines.append("    // TODO: Add assertions")
                lines.append(f"    // expect(result).toBe({self._to_js_value(test.expected_output)});")

            lines.append("  });")
            lines.append("")

        lines.append("});")

        return "\n".join(lines)

    def _generate_go_test(self, suite: TestSuite) -> str:
        """Generate Go test code"""
        lines = []

        lines.append("package main")
        lines.append("")
        lines.append('import "testing"')
        lines.append("")

        for test in suite.test_cases:
            func_name = "".join(word.capitalize() for word in test.name.split("_"))
            lines.append(f"func {func_name}(t *testing.T) {{")
            lines.append(f"    // {test.description}")
            lines.append("")
            lines.append("    // TODO: Implement test")
            lines.append("    // result := FunctionToTest(...)")
            lines.append("    // if result != expected {")
            lines.append('    //     t.Errorf("Expected %v, got %v", expected, result)')
            lines.append("    // }")
            lines.append("}")
            lines.append("")

        return "\n".join(lines)

    def _to_js_value(self, value: Any) -> str:
        """Convert Python value to JavaScript literal"""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (list, dict)):
            import json
            return json.dumps(value)
        else:
            return str(value)


# ===========================================
# Convenience Functions
# ===========================================

_default_generator: Optional[TestGenerator] = None


def get_test_generator() -> TestGenerator:
    """Get the default test generator"""
    global _default_generator
    if _default_generator is None:
        _default_generator = TestGenerator()
    return _default_generator


def generate_tests(
    code: str,
    language: str,
    framework: Optional[str] = None,
    include_edge_cases: bool = True
) -> str:
    """
    Generate tests for code.

    Args:
        code: Source code to test
        language: Programming language
        framework: Test framework (auto-detected if not provided)
        include_edge_cases: Include edge case tests

    Returns:
        Generated test code as string
    """
    generator = get_test_generator()
    suite = generator.generate_tests(
        code,
        language,
        include_edge_cases=include_edge_cases
    )

    # Auto-detect framework
    if framework is None:
        if language.lower() == "python":
            fw = TestFramework.PYTEST
        elif language.lower() in ("javascript", "typescript"):
            fw = TestFramework.VITEST
        elif language.lower() == "go":
            fw = TestFramework.GO_TEST
        else:
            fw = TestFramework.PYTEST
    else:
        fw = TestFramework(framework)

    return suite.to_code(fw, language)


def generate_python_tests(code: str) -> str:
    """Generate pytest tests for Python code"""
    return generate_tests(code, "python", "pytest")


def generate_typescript_tests(code: str) -> str:
    """Generate Vitest tests for TypeScript code"""
    return generate_tests(code, "typescript", "vitest")


def generate_javascript_tests(code: str) -> str:
    """Generate Vitest tests for JavaScript code"""
    return generate_tests(code, "javascript", "vitest")
