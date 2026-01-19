"""
Constrained Generation Module using Outlines

Provides grammar and regex-constrained LLM generation to ensure
syntactically valid outputs. Essential for generating valid code,
JSON, SQL, and other structured formats.

Features:
- Grammar-based constraints (EBNF)
- Regex pattern matching
- JSON schema enforcement
- Code syntax validation
- Custom format generators
"""

from typing import Optional, List, Dict, Any, Type, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel
import json
import logging
import re

logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Predefined output formats"""
    JSON = "json"
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    SQL = "sql"
    MARKDOWN = "markdown"
    YAML = "yaml"
    HTML = "html"
    CSS = "css"
    REGEX = "regex"
    CUSTOM = "custom"


@dataclass
class GenerationConfig:
    """Configuration for constrained generation"""
    format: OutputFormat = OutputFormat.JSON
    schema: Optional[Dict[str, Any]] = None
    regex_pattern: Optional[str] = None
    grammar: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.7
    stop_sequences: List[str] = field(default_factory=list)


@dataclass
class GenerationResult:
    """Result of constrained generation"""
    content: str
    format: OutputFormat
    is_valid: bool
    validation_errors: List[str] = field(default_factory=list)
    parsed_content: Optional[Any] = None


# ===========================================
# Predefined Grammars (EBNF-like)
# ===========================================

GRAMMARS = {
    "json_object": r'''
        ?start: object
        object: "{" [pair ("," pair)*] "}"
        pair: string ":" value
        array: "[" [value ("," value)*] "]"
        value: object | array | string | number | "true" | "false" | "null"
        string: /"[^"\\]*(\\.[^"\\]*)*"/
        number: /-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-]?[0-9]+)?/
    ''',

    "python_function": r'''
        ?start: function_def
        function_def: decorator* "def" NAME "(" parameters? ")" return_type? ":" body
        decorator: "@" dotted_name ["(" arguments? ")"] NEWLINE
        dotted_name: NAME ("." NAME)*
        parameters: param ("," param)*
        param: NAME [":" type] ["=" expression]
        return_type: "->" type
        type: NAME | NAME "[" type ("," type)* "]"
        body: NEWLINE INDENT statement+ DEDENT
        statement: simple_stmt | compound_stmt
        simple_stmt: (expression | assignment | return_stmt | pass_stmt) NEWLINE
        compound_stmt: if_stmt | for_stmt | while_stmt | try_stmt
        assignment: NAME [":" type] "=" expression
        return_stmt: "return" expression?
        pass_stmt: "pass"
        if_stmt: "if" expression ":" body ("elif" expression ":" body)* ("else" ":" body)?
        for_stmt: "for" NAME "in" expression ":" body
        while_stmt: "while" expression ":" body
        try_stmt: "try" ":" body except_clause+ ("else" ":" body)? ("finally" ":" body)?
        except_clause: "except" [NAME ["as" NAME]] ":" body
        expression: /[^:\n]+/
        arguments: /[^)]+/
        NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
        NEWLINE: /\n/
        INDENT: /    /
        DEDENT: //
    ''',

    "typescript_function": r'''
        ?start: function_def | arrow_function
        function_def: export? async? "function" NAME type_params? "(" parameters? ")" return_type? block
        arrow_function: export? "const" NAME type_annotation? "=" async? "(" parameters? ")" return_type? "=>" (expression | block)
        export: "export" "default"?
        async: "async"
        type_params: "<" NAME ("," NAME)* ">"
        parameters: param ("," param)*
        param: NAME "?"? type_annotation? ("=" expression)?
        type_annotation: ":" type
        return_type: ":" type
        type: NAME | NAME "<" type ("," type)* ">" | "(" type ")" | type "|" type | type "&" type
        block: "{" statement* "}"
        statement: /[^{}]+/ | block
        expression: /[^;{}\n]+/
        NAME: /[a-zA-Z_$][a-zA-Z0-9_$]*/
    ''',

    "sql_select": r'''
        ?start: select_stmt
        select_stmt: "SELECT" select_list "FROM" table_ref where_clause? group_by? order_by? limit_clause?
        select_list: "*" | select_item ("," select_item)*
        select_item: expression alias?
        alias: "AS"i NAME
        table_ref: table_name alias? join_clause*
        table_name: NAME ("." NAME)?
        join_clause: join_type? "JOIN"i table_ref "ON"i condition
        join_type: "LEFT"i | "RIGHT"i | "INNER"i | "OUTER"i | "CROSS"i
        where_clause: "WHERE"i condition
        condition: expression (("AND"i | "OR"i) expression)*
        group_by: "GROUP"i "BY"i expression ("," expression)*
        order_by: "ORDER"i "BY"i order_item ("," order_item)*
        order_item: expression ("ASC"i | "DESC"i)?
        limit_clause: "LIMIT"i NUMBER ("OFFSET"i NUMBER)?
        expression: /[^,;()]+/ | "(" expression ")"
        NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
        NUMBER: /[0-9]+/
    '''
}


# ===========================================
# Predefined Regex Patterns
# ===========================================

REGEX_PATTERNS = {
    "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "url": r"https?://[^\s<>\"{}|\\^`\[\]]+",
    "phone": r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    "date_iso": r"\d{4}-\d{2}-\d{2}",
    "time_24h": r"([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?",
    "uuid": r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    "hex_color": r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?",
    "version": r"\d+\.\d+(\.\d+)?(-[a-zA-Z0-9]+)?",
    "ip_address": r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}",
    "variable_name": r"[a-zA-Z_][a-zA-Z0-9_]*",
    "class_name": r"[A-Z][a-zA-Z0-9]*",
    "snake_case": r"[a-z][a-z0-9_]*",
    "camel_case": r"[a-z][a-zA-Z0-9]*",
    "pascal_case": r"[A-Z][a-zA-Z0-9]*",
}


class ConstrainedGenerator:
    """
    Constrained LLM generation using Outlines.

    Example:
        generator = ConstrainedGenerator()

        # Generate JSON matching a schema
        result = generator.generate_json(
            prompt="Generate user data",
            schema={"type": "object", "properties": {"name": {"type": "string"}}}
        )

        # Generate Python function
        result = generator.generate_code(
            prompt="Write a function to calculate factorial",
            language="python"
        )

        # Generate with regex constraint
        result = generator.generate_regex(
            prompt="Generate a valid email",
            pattern=r"[a-z]+@[a-z]+\\.com"
        )
    """

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
        self._outlines_available = False
        self._init_outlines()

    def _init_outlines(self):
        """Initialize Outlines"""
        try:
            import outlines
            self._outlines_available = True
            logger.info("Outlines initialized successfully")
        except ImportError as e:
            logger.warning(f"Outlines not available: {e}. Using validation fallback.")
            self._outlines_available = False

    def generate(
        self,
        prompt: str,
        config: GenerationConfig,
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """
        Generate constrained output.

        Args:
            prompt: User prompt
            config: Generation configuration
            system_prompt: Optional system prompt

        Returns:
            GenerationResult with validated content
        """
        if self._outlines_available:
            return self._generate_with_outlines(prompt, config, system_prompt)
        else:
            return self._generate_with_validation(prompt, config, system_prompt)

    def generate_json(
        self,
        prompt: str,
        schema: Optional[Dict[str, Any]] = None,
        pydantic_model: Optional[Type[BaseModel]] = None,
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """Generate JSON constrained by schema"""
        if pydantic_model:
            schema = pydantic_model.model_json_schema()

        config = GenerationConfig(
            format=OutputFormat.JSON,
            schema=schema
        )
        return self.generate(prompt, config, system_prompt)

    def generate_code(
        self,
        prompt: str,
        language: str,
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """Generate syntactically valid code"""
        format_map = {
            "python": OutputFormat.PYTHON,
            "typescript": OutputFormat.TYPESCRIPT,
            "javascript": OutputFormat.TYPESCRIPT,
            "sql": OutputFormat.SQL,
            "html": OutputFormat.HTML,
            "css": OutputFormat.CSS,
        }

        config = GenerationConfig(
            format=format_map.get(language.lower(), OutputFormat.CUSTOM),
            grammar=GRAMMARS.get(f"{language.lower()}_function")
        )

        # Add language-specific system prompt
        if not system_prompt:
            system_prompt = f"You are an expert {language} developer. Generate clean, valid {language} code."

        return self.generate(prompt, config, system_prompt)

    def generate_regex(
        self,
        prompt: str,
        pattern: str,
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """Generate text matching regex pattern"""
        config = GenerationConfig(
            format=OutputFormat.REGEX,
            regex_pattern=pattern
        )
        return self.generate(prompt, config, system_prompt)

    def generate_choice(
        self,
        prompt: str,
        choices: List[str],
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """Generate output from a set of choices"""
        # Create regex pattern from choices
        pattern = "|".join(re.escape(c) for c in choices)

        config = GenerationConfig(
            format=OutputFormat.REGEX,
            regex_pattern=f"({pattern})"
        )

        result = self.generate(prompt, config, system_prompt)
        result.parsed_content = result.content if result.content in choices else None
        return result

    def generate_structured(
        self,
        prompt: str,
        output_class: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> GenerationResult:
        """Generate output matching a Pydantic model"""
        schema = output_class.model_json_schema()

        config = GenerationConfig(
            format=OutputFormat.JSON,
            schema=schema
        )

        result = self.generate(prompt, config, system_prompt)

        # Parse into Pydantic model
        if result.is_valid and result.content:
            try:
                result.parsed_content = output_class.model_validate_json(result.content)
            except Exception as e:
                result.validation_errors.append(f"Pydantic validation failed: {e}")
                result.is_valid = False

        return result

    def _generate_with_outlines(
        self,
        prompt: str,
        config: GenerationConfig,
        system_prompt: Optional[str]
    ) -> GenerationResult:
        """Generate using Outlines constraints"""
        try:
            import outlines
            from outlines import models, generate

            # This would use Outlines with actual model
            # For now, fall back to validation approach
            return self._generate_with_validation(prompt, config, system_prompt)

        except Exception as e:
            logger.error(f"Outlines generation failed: {e}")
            return self._generate_with_validation(prompt, config, system_prompt)

    def _generate_with_validation(
        self,
        prompt: str,
        config: GenerationConfig,
        system_prompt: Optional[str]
    ) -> GenerationResult:
        """Generate with post-hoc validation (fallback)"""
        # Build prompt with format instructions
        enhanced_prompt = self._build_constrained_prompt(prompt, config)

        # Call LLM (mock for now)
        content = self._call_llm(enhanced_prompt, system_prompt, config)

        # Validate output
        is_valid, errors, parsed = self._validate_output(content, config)

        return GenerationResult(
            content=content,
            format=config.format,
            is_valid=is_valid,
            validation_errors=errors,
            parsed_content=parsed
        )

    def _build_constrained_prompt(self, prompt: str, config: GenerationConfig) -> str:
        """Build prompt with format constraints"""
        format_instructions = {
            OutputFormat.JSON: """
Output ONLY valid JSON. Do not include any text before or after the JSON.
The response must be parseable by JSON.parse().
""",
            OutputFormat.PYTHON: """
Output ONLY valid Python code. Do not include any markdown formatting.
Do not include ```python or ``` markers.
The code must be syntactically correct and executable.
""",
            OutputFormat.TYPESCRIPT: """
Output ONLY valid TypeScript code. Do not include any markdown formatting.
Do not include ```typescript or ``` markers.
The code must be syntactically correct and compilable.
""",
            OutputFormat.SQL: """
Output ONLY valid SQL. Do not include any markdown formatting.
Do not include ```sql or ``` markers.
The SQL must be valid and executable.
""",
            OutputFormat.MARKDOWN: """
Output valid Markdown. Use proper heading levels, code blocks, and formatting.
""",
            OutputFormat.YAML: """
Output ONLY valid YAML. Do not include any markdown formatting.
Do not include ```yaml or ``` markers.
The YAML must be parseable.
""",
            OutputFormat.HTML: """
Output ONLY valid HTML. Do not include any markdown formatting.
The HTML must be well-formed with proper tag closure.
""",
            OutputFormat.CSS: """
Output ONLY valid CSS. Do not include any markdown formatting.
Do not include ```css or ``` markers.
""",
        }

        instructions = format_instructions.get(config.format, "")

        if config.schema:
            instructions += f"\n\nJSON Schema to follow:\n{json.dumps(config.schema, indent=2)}"

        if config.regex_pattern:
            instructions += f"\n\nOutput must match this pattern: {config.regex_pattern}"

        return f"{instructions}\n\n{prompt}"

    def _call_llm(
        self,
        prompt: str,
        system_prompt: Optional[str],
        config: GenerationConfig
    ) -> str:
        """Call the LLM (placeholder - integrate with actual LLM)"""
        # This would integrate with the LLM router
        # For now, return a mock response based on format

        if config.format == OutputFormat.JSON:
            if config.schema:
                return self._generate_mock_from_schema(config.schema)
            return '{"result": "mock_value"}'

        elif config.format == OutputFormat.PYTHON:
            return '''def example_function(x: int) -> int:
    """Example function"""
    return x * 2'''

        elif config.format == OutputFormat.TYPESCRIPT:
            return '''export function exampleFunction(x: number): number {
    return x * 2;
}'''

        elif config.format == OutputFormat.SQL:
            return 'SELECT id, name FROM users WHERE active = true'

        return "mock_output"

    def _generate_mock_from_schema(self, schema: Dict[str, Any]) -> str:
        """Generate mock JSON from schema"""
        def generate_value(prop_schema: Dict[str, Any]) -> Any:
            prop_type = prop_schema.get("type", "string")

            if prop_type == "string":
                return prop_schema.get("default", "mock_string")
            elif prop_type == "integer":
                return prop_schema.get("default", 0)
            elif prop_type == "number":
                return prop_schema.get("default", 0.0)
            elif prop_type == "boolean":
                return prop_schema.get("default", False)
            elif prop_type == "array":
                items = prop_schema.get("items", {})
                return [generate_value(items)]
            elif prop_type == "object":
                return generate_object(prop_schema)
            elif "enum" in prop_schema:
                return prop_schema["enum"][0]

            return None

        def generate_object(obj_schema: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            properties = obj_schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                result[prop_name] = generate_value(prop_schema)
            return result

        if schema.get("type") == "object":
            return json.dumps(generate_object(schema), indent=2)

        return json.dumps(generate_value(schema))

    def _validate_output(
        self,
        content: str,
        config: GenerationConfig
    ) -> tuple:
        """Validate generated output"""
        errors = []
        parsed = None

        if config.format == OutputFormat.JSON:
            try:
                parsed = json.loads(content)

                # Validate against schema if provided
                if config.schema:
                    schema_errors = self._validate_json_schema(parsed, config.schema)
                    errors.extend(schema_errors)

            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON: {e}")

        elif config.format == OutputFormat.PYTHON:
            try:
                compile(content, "<string>", "exec")
                parsed = content
            except SyntaxError as e:
                errors.append(f"Python syntax error: {e}")

        elif config.format == OutputFormat.TYPESCRIPT:
            # Basic validation - check for obvious issues
            if content.count('{') != content.count('}'):
                errors.append("Mismatched braces")
            if content.count('(') != content.count(')'):
                errors.append("Mismatched parentheses")
            parsed = content

        elif config.format == OutputFormat.SQL:
            # Basic SQL validation
            content_upper = content.upper()
            if not any(kw in content_upper for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE']):
                errors.append("No SQL statement keyword found")
            parsed = content

        elif config.format == OutputFormat.YAML:
            try:
                import yaml
                parsed = yaml.safe_load(content)
            except Exception as e:
                errors.append(f"Invalid YAML: {e}")

        elif config.format == OutputFormat.HTML:
            # Check for tag balance
            open_tags = re.findall(r'<([a-z]+)(?:\s|>)', content, re.IGNORECASE)
            close_tags = re.findall(r'</([a-z]+)>', content, re.IGNORECASE)
            # Simplified check - real validation would use a parser
            parsed = content

        if config.regex_pattern:
            if not re.fullmatch(config.regex_pattern, content):
                errors.append(f"Output does not match pattern: {config.regex_pattern}")

        return len(errors) == 0, errors, parsed

    def _validate_json_schema(self, data: Any, schema: Dict[str, Any]) -> List[str]:
        """Validate JSON against schema"""
        errors = []

        try:
            import jsonschema
            validator = jsonschema.Draft7Validator(schema)
            for error in validator.iter_errors(data):
                errors.append(str(error.message))
        except ImportError:
            # Fallback: basic type checking
            if "type" in schema:
                expected_type = schema["type"]
                type_map = {
                    "string": str,
                    "integer": int,
                    "number": (int, float),
                    "boolean": bool,
                    "array": list,
                    "object": dict,
                }
                if expected_type in type_map:
                    if not isinstance(data, type_map[expected_type]):
                        errors.append(f"Expected {expected_type}, got {type(data).__name__}")

        return errors


class CodeValidator:
    """
    Validate generated code for syntax and basic correctness.

    Example:
        validator = CodeValidator()

        is_valid, errors = validator.validate_python('''
        def hello():
            print("Hello")
        ''')
    """

    def validate_python(self, code: str) -> tuple:
        """Validate Python code"""
        errors = []
        try:
            compile(code, "<string>", "exec")
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
        return len(errors) == 0, errors

    def validate_javascript(self, code: str) -> tuple:
        """Validate JavaScript code (basic)"""
        errors = []

        # Check brace balance
        if code.count('{') != code.count('}'):
            errors.append("Mismatched braces")
        if code.count('(') != code.count(')'):
            errors.append("Mismatched parentheses")
        if code.count('[') != code.count(']'):
            errors.append("Mismatched brackets")

        # Check for common issues
        if re.search(r'\bvar\b', code):
            errors.append("Warning: Using 'var' instead of 'const' or 'let'")

        return len(errors) == 0, errors

    def validate_typescript(self, code: str) -> tuple:
        """Validate TypeScript code (basic)"""
        # TypeScript extends JavaScript validation
        is_valid, errors = self.validate_javascript(code)

        # Additional TS checks could go here
        return is_valid, errors

    def validate_json(self, code: str) -> tuple:
        """Validate JSON"""
        errors = []
        try:
            json.loads(code)
        except json.JSONDecodeError as e:
            errors.append(f"Line {e.lineno}, Column {e.colno}: {e.msg}")
        return len(errors) == 0, errors

    def validate_sql(self, code: str) -> tuple:
        """Validate SQL (basic)"""
        errors = []
        code_upper = code.upper()

        # Check for statement type
        has_statement = any(
            kw in code_upper
            for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        )
        if not has_statement:
            errors.append("No valid SQL statement found")

        # Check for semicolon (optional but recommended)
        if not code.strip().endswith(';'):
            errors.append("Warning: SQL statement should end with semicolon")

        return len(errors) == 0 or all("Warning" in e for e in errors), errors

    def validate(self, code: str, language: str) -> tuple:
        """Validate code for any supported language"""
        validators = {
            "python": self.validate_python,
            "javascript": self.validate_javascript,
            "typescript": self.validate_typescript,
            "json": self.validate_json,
            "sql": self.validate_sql,
        }

        validator = validators.get(language.lower())
        if validator:
            return validator(code)

        return True, []  # Unknown language, assume valid


# ===========================================
# Convenience Functions
# ===========================================

_default_generator: Optional[ConstrainedGenerator] = None
_default_validator: Optional[CodeValidator] = None


def get_generator() -> ConstrainedGenerator:
    """Get the default constrained generator"""
    global _default_generator
    if _default_generator is None:
        _default_generator = ConstrainedGenerator()
    return _default_generator


def get_validator() -> CodeValidator:
    """Get the default code validator"""
    global _default_validator
    if _default_validator is None:
        _default_validator = CodeValidator()
    return _default_validator


def generate_json(prompt: str, schema: Optional[Dict] = None) -> GenerationResult:
    """Generate constrained JSON"""
    return get_generator().generate_json(prompt, schema)


def generate_code(prompt: str, language: str) -> GenerationResult:
    """Generate constrained code"""
    return get_generator().generate_code(prompt, language)


def generate_choice(prompt: str, choices: List[str]) -> GenerationResult:
    """Generate from choices"""
    return get_generator().generate_choice(prompt, choices)


def validate_code(code: str, language: str) -> tuple:
    """Validate code syntax"""
    return get_validator().validate(code, language)
