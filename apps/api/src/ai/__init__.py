"""
AI Enhancement Modules for Code Weaver Pro

This package provides advanced AI capabilities for code generation,
parsing, search, validation, and constrained generation.

Modules:
- structured_output: Instructor-based structured LLM outputs
- code_parser: Tree-sitter based code parsing and AST analysis
- vector_search: Chroma-based semantic code search
- constrained_generation: Outlines-based constrained generation
- code_validation: Ruff/Semgrep code quality and security validation
- code_executor: Safe sandboxed code execution with feedback loops
- prompt_optimizer: DSPy-based automatic prompt optimization
- test_generator: Automatic test generation for code verification
"""

from typing import TYPE_CHECKING

# Lazy imports to avoid loading all dependencies at once
if TYPE_CHECKING:
    from .structured_output import (
        StructuredOutputClient,
        ProjectStructure,
        CodeFile,
        TaskPlan,
        AnalysisResult,
        CodeReview,
        get_structured_client,
        generate_project,
        analyze_code,
        plan_task,
    )
    from .code_parser import (
        CodeParser,
        ParseResult,
        FunctionDef,
        ClassDef,
        ImportDef,
        Language,
        get_parser,
        parse_code,
        parse_file,
        extract_functions,
        extract_classes,
        get_code_metrics,
    )
    from .vector_search import (
        VectorStore,
        CodeIndexer,
        DocumentationIndexer,
        SearchResult,
        Document,
        CollectionType,
        get_vector_store,
        get_code_indexer,
        search_code,
        search_docs,
        index_project,
    )
    from .constrained_generation import (
        ConstrainedGenerator,
        GenerationResult,
        GenerationConfig,
        OutputFormat,
        CodeValidator as ConstraintValidator,
        get_generator,
        generate_json,
        generate_code,
        generate_choice,
        validate_code as validate_generated_code,
    )
    from .code_validation import (
        CodeValidationPipeline,
        ValidationResult,
        CodeIssue,
        Severity,
        IssueCategory,
        RuffValidator,
        SemgrepValidator,
        ESLintValidator,
        get_validation_pipeline,
        validate_code,
        validate_and_fix,
        quick_check,
        validate_python,
        validate_typescript,
        validate_javascript,
    )
    from .code_executor import (
        CodeExecutor,
        ExecutionResult,
        ExecutionConfig,
        ExecutionStatus,
        MultiFileExecutor,
        TestRunner,
        get_executor,
        get_test_runner,
        execute_code,
        execute_python,
        execute_javascript,
        run_tests,
    )
    from .prompt_optimizer import (
        PromptOptimizer,
        PromptTemplate,
        OptimizationResult,
        ExampleStore,
        SelfImprovingAgent,
        get_optimizer,
        create_code_prompt,
        create_fix_prompt,
        record_success,
        record_failure,
    )
    from .test_generator import (
        TestGenerator,
        TestSuite,
        TestCase,
        TestType,
        TestFramework,
        get_test_generator,
        generate_tests,
        generate_python_tests,
        generate_typescript_tests,
        generate_javascript_tests,
    )


def __getattr__(name: str):
    """Lazy import of submodules"""
    if name in (
        "StructuredOutputClient", "ProjectStructure", "CodeFile", "TaskPlan",
        "AnalysisResult", "CodeReview", "get_structured_client", "generate_project",
        "analyze_code", "plan_task"
    ):
        from . import structured_output
        return getattr(structured_output, name)

    if name in (
        "CodeParser", "ParseResult", "FunctionDef", "ClassDef", "ImportDef",
        "Language", "get_parser", "parse_code", "parse_file", "extract_functions",
        "extract_classes", "get_code_metrics"
    ):
        from . import code_parser
        return getattr(code_parser, name)

    if name in (
        "VectorStore", "CodeIndexer", "DocumentationIndexer", "SearchResult",
        "Document", "CollectionType", "get_vector_store", "get_code_indexer",
        "search_code", "search_docs", "index_project"
    ):
        from . import vector_search
        return getattr(vector_search, name)

    if name in (
        "ConstrainedGenerator", "GenerationResult", "GenerationConfig",
        "OutputFormat", "ConstraintValidator", "get_generator", "generate_json",
        "generate_code", "generate_choice", "validate_generated_code"
    ):
        from . import constrained_generation
        if name == "validate_generated_code":
            return constrained_generation.validate_code
        if name == "ConstraintValidator":
            return constrained_generation.CodeValidator
        return getattr(constrained_generation, name)

    if name in (
        "CodeValidationPipeline", "ValidationResult", "CodeIssue", "Severity",
        "IssueCategory", "RuffValidator", "SemgrepValidator", "ESLintValidator",
        "get_validation_pipeline", "validate_code", "validate_and_fix",
        "quick_check", "validate_python", "validate_typescript", "validate_javascript"
    ):
        from . import code_validation
        return getattr(code_validation, name)

    if name in (
        "CodeExecutor", "ExecutionResult", "ExecutionConfig", "ExecutionStatus",
        "MultiFileExecutor", "TestRunner", "get_executor", "get_test_runner",
        "execute_code", "execute_python", "execute_javascript", "run_tests"
    ):
        from . import code_executor
        return getattr(code_executor, name)

    if name in (
        "PromptOptimizer", "PromptTemplate", "OptimizationResult", "ExampleStore",
        "SelfImprovingAgent", "get_optimizer", "create_code_prompt", "create_fix_prompt",
        "record_success", "record_failure"
    ):
        from . import prompt_optimizer
        return getattr(prompt_optimizer, name)

    if name in (
        "TestGenerator", "TestSuite", "TestCase", "TestType", "TestFramework",
        "get_test_generator", "generate_tests", "generate_python_tests",
        "generate_typescript_tests", "generate_javascript_tests"
    ):
        from . import test_generator
        return getattr(test_generator, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Structured Output
    "StructuredOutputClient",
    "ProjectStructure",
    "CodeFile",
    "TaskPlan",
    "AnalysisResult",
    "CodeReview",
    "get_structured_client",
    "generate_project",
    "analyze_code",
    "plan_task",

    # Code Parser
    "CodeParser",
    "ParseResult",
    "FunctionDef",
    "ClassDef",
    "ImportDef",
    "Language",
    "get_parser",
    "parse_code",
    "parse_file",
    "extract_functions",
    "extract_classes",
    "get_code_metrics",

    # Vector Search
    "VectorStore",
    "CodeIndexer",
    "DocumentationIndexer",
    "SearchResult",
    "Document",
    "CollectionType",
    "get_vector_store",
    "get_code_indexer",
    "search_code",
    "search_docs",
    "index_project",

    # Constrained Generation
    "ConstrainedGenerator",
    "GenerationResult",
    "GenerationConfig",
    "OutputFormat",
    "ConstraintValidator",
    "get_generator",
    "generate_json",
    "generate_code",
    "generate_choice",
    "validate_generated_code",

    # Code Validation
    "CodeValidationPipeline",
    "ValidationResult",
    "CodeIssue",
    "Severity",
    "IssueCategory",
    "RuffValidator",
    "SemgrepValidator",
    "ESLintValidator",
    "get_validation_pipeline",
    "validate_code",
    "validate_and_fix",
    "quick_check",
    "validate_python",
    "validate_typescript",
    "validate_javascript",

    # Code Executor
    "CodeExecutor",
    "ExecutionResult",
    "ExecutionConfig",
    "ExecutionStatus",
    "MultiFileExecutor",
    "TestRunner",
    "get_executor",
    "get_test_runner",
    "execute_code",
    "execute_python",
    "execute_javascript",
    "run_tests",

    # Prompt Optimizer
    "PromptOptimizer",
    "PromptTemplate",
    "OptimizationResult",
    "ExampleStore",
    "SelfImprovingAgent",
    "get_optimizer",
    "create_code_prompt",
    "create_fix_prompt",
    "record_success",
    "record_failure",

    # Test Generator
    "TestGenerator",
    "TestSuite",
    "TestCase",
    "TestType",
    "TestFramework",
    "get_test_generator",
    "generate_tests",
    "generate_python_tests",
    "generate_typescript_tests",
    "generate_javascript_tests",
]
