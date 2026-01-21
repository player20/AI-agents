"""
Code Validator Service

Validates generated code BEFORE sending to WebContainer to catch common errors.
This provides pre-flight validation to prevent white page failures.
"""

import re
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(Enum):
    ERROR = "error"      # Will definitely break WebContainer
    WARNING = "warning"  # Might cause issues, should fix
    INFO = "info"        # Suggestion for improvement


@dataclass
class ValidationIssue:
    """A single validation issue found in the code"""
    file_path: str
    line_number: Optional[int]
    severity: ValidationSeverity
    code: str  # e.g., "NEXT_IMAGE_FORBIDDEN"
    message: str
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "line_number": self.line_number,
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "suggestion": self.suggestion
        }


@dataclass
class ValidationResult:
    """Result of validating a project's files"""
    is_valid: bool
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)

    @property
    def all_issues(self) -> List[ValidationIssue]:
        return self.errors + self.warnings

    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }


# Forbidden patterns that WILL break WebContainer
FORBIDDEN_PATTERNS: List[Tuple[str, str, str, str]] = [
    # (regex_pattern, error_code, message, suggestion)

    # Next.js Image - doesn't work in WebContainer
    (
        r"from\s+['\"]next/image['\"]",
        "NEXT_IMAGE_FORBIDDEN",
        "next/image is not supported in WebContainer",
        "Use regular <img> tags instead: <img src={...} alt={...} className=\"...\" />"
    ),
    (
        r"import\s+Image\s+from\s+['\"]next/image['\"]",
        "NEXT_IMAGE_FORBIDDEN",
        "next/image is not supported in WebContainer",
        "Use regular <img> tags instead"
    ),

    # next/font - doesn't work in WebContainer
    (
        r"from\s+['\"]next/font",
        "NEXT_FONT_FORBIDDEN",
        "next/font is not supported in WebContainer",
        "Use Google Fonts via <link> in layout.tsx or standard system fonts"
    ),

    # Wrong useRouter import (next/router vs next/navigation)
    (
        r"from\s+['\"]next/router['\"]",
        "WRONG_ROUTER_IMPORT",
        "next/router is for Pages Router, not App Router",
        "Use: import { useRouter } from 'next/navigation'"
    ),

    # shadcn/ui classes without proper config
    (
        r"(?:className|class)=['\"][^'\"]*\b(?:border-border|bg-background|text-foreground|bg-muted|text-muted|bg-card|text-card|bg-popover|text-popover|bg-primary|text-primary|bg-secondary|text-secondary|bg-accent|text-accent|bg-destructive|text-destructive)\b",
        "SHADCN_CLASSES_FORBIDDEN",
        "shadcn/ui classes require specific Tailwind config not in template",
        "Use standard Tailwind classes: bg-white, bg-gray-100, text-gray-900, border-gray-200, etc."
    ),

    # SWC-specific imports
    (
        r"@swc/",
        "SWC_FORBIDDEN",
        "SWC binaries don't work in WebContainer",
        "Use Babel via .babelrc for transpilation"
    ),

    # Native Node modules that don't work in WebContainer
    (
        r"require\(['\"](?:fs|path|child_process|os|crypto|net|dgram|dns|tls|cluster)['\"]",
        "NATIVE_MODULE_FORBIDDEN",
        "Native Node.js modules don't work in WebContainer browser environment",
        "Use browser-compatible alternatives or polyfills"
    ),
    (
        r"from\s+['\"](?:fs|path|child_process|os|crypto|net|dgram|dns|tls|cluster)['\"]",
        "NATIVE_MODULE_FORBIDDEN",
        "Native Node.js modules don't work in WebContainer browser environment",
        "Use browser-compatible alternatives or polyfills"
    ),
]

# React hooks that require 'use client' directive
REACT_HOOKS = [
    "useState", "useEffect", "useContext", "useReducer", "useCallback",
    "useMemo", "useRef", "useLayoutEffect", "useImperativeHandle",
    "useDebugValue", "useDeferredValue", "useTransition", "useId",
    "useSyncExternalStore", "useInsertionEffect", "useRouter", "usePathname",
    "useSearchParams", "useParams"
]


class CodeValidator:
    """Validates generated code before WebContainer execution"""

    def __init__(self):
        self.forbidden_patterns = FORBIDDEN_PATTERNS
        self.react_hooks = REACT_HOOKS

    def validate_project(self, files: Dict[str, str]) -> ValidationResult:
        """
        Validate all files in a project.

        Args:
            files: Dictionary mapping file paths to content

        Returns:
            ValidationResult with all issues found
        """
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []

        # Check package.json exists and is valid
        pkg_issues = self._validate_package_json(files)
        errors.extend([i for i in pkg_issues if i.severity == ValidationSeverity.ERROR])
        warnings.extend([i for i in pkg_issues if i.severity == ValidationSeverity.WARNING])

        # Check tsconfig.json has proper path aliases
        ts_issues = self._validate_tsconfig(files)
        errors.extend([i for i in ts_issues if i.severity == ValidationSeverity.ERROR])
        warnings.extend([i for i in ts_issues if i.severity == ValidationSeverity.WARNING])

        # Check each source file
        for file_path, content in files.items():
            if self._is_source_file(file_path):
                file_issues = self._validate_file(file_path, content, files)
                errors.extend([i for i in file_issues if i.severity == ValidationSeverity.ERROR])
                warnings.extend([i for i in file_issues if i.severity == ValidationSeverity.WARNING])

        # Check for missing dependencies
        dep_issues = self._validate_dependencies(files)
        errors.extend([i for i in dep_issues if i.severity == ValidationSeverity.ERROR])
        warnings.extend([i for i in dep_issues if i.severity == ValidationSeverity.WARNING])

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _is_source_file(self, path: str) -> bool:
        """Check if file is a source file we should validate"""
        extensions = [".tsx", ".ts", ".jsx", ".js", ".css"]
        return any(path.endswith(ext) for ext in extensions)

    def _validate_package_json(self, files: Dict[str, str]) -> List[ValidationIssue]:
        """Validate package.json exists and has required fields"""
        issues = []

        if "package.json" not in files:
            issues.append(ValidationIssue(
                file_path="package.json",
                line_number=None,
                severity=ValidationSeverity.ERROR,
                code="MISSING_PACKAGE_JSON",
                message="package.json is missing",
                suggestion="Add a package.json with project dependencies"
            ))
            return issues

        try:
            pkg = json.loads(files["package.json"])
        except json.JSONDecodeError as e:
            issues.append(ValidationIssue(
                file_path="package.json",
                line_number=None,
                severity=ValidationSeverity.ERROR,
                code="INVALID_PACKAGE_JSON",
                message=f"package.json is not valid JSON: {e}",
                suggestion="Fix the JSON syntax in package.json"
            ))
            return issues

        # Check for required scripts
        scripts = pkg.get("scripts", {})
        if "dev" not in scripts:
            issues.append(ValidationIssue(
                file_path="package.json",
                line_number=None,
                severity=ValidationSeverity.ERROR,
                code="MISSING_DEV_SCRIPT",
                message="package.json missing 'dev' script",
                suggestion="Add: \"scripts\": { \"dev\": \"next dev\" }"
            ))

        # Check for Next.js dependency
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        if "next" not in deps:
            issues.append(ValidationIssue(
                file_path="package.json",
                line_number=None,
                severity=ValidationSeverity.ERROR,
                code="MISSING_NEXT_DEPENDENCY",
                message="Next.js is not in dependencies",
                suggestion="Add next@13.5.6 to dependencies"
            ))

        # Check Next.js version is WebContainer compatible
        next_version = deps.get("next", "")
        if next_version and not self._is_compatible_next_version(next_version):
            issues.append(ValidationIssue(
                file_path="package.json",
                line_number=None,
                severity=ValidationSeverity.WARNING,
                code="NEXT_VERSION_WARNING",
                message=f"Next.js version {next_version} may have WebContainer issues",
                suggestion="Use next@13.5.6 for best WebContainer compatibility"
            ))

        return issues

    def _is_compatible_next_version(self, version: str) -> bool:
        """Check if Next.js version is WebContainer compatible"""
        # Remove ^ or ~ prefix
        clean_version = version.lstrip("^~")
        # 13.5.x versions are known to work well
        return clean_version.startswith("13.5")

    def _validate_tsconfig(self, files: Dict[str, str]) -> List[ValidationIssue]:
        """Validate tsconfig.json has proper path aliases"""
        issues = []

        if "tsconfig.json" not in files:
            issues.append(ValidationIssue(
                file_path="tsconfig.json",
                line_number=None,
                severity=ValidationSeverity.WARNING,
                code="MISSING_TSCONFIG",
                message="tsconfig.json is missing",
                suggestion="Add tsconfig.json for TypeScript support"
            ))
            return issues

        try:
            tsconfig = json.loads(files["tsconfig.json"])
        except json.JSONDecodeError:
            issues.append(ValidationIssue(
                file_path="tsconfig.json",
                line_number=None,
                severity=ValidationSeverity.ERROR,
                code="INVALID_TSCONFIG",
                message="tsconfig.json is not valid JSON",
                suggestion="Fix JSON syntax - note: tsconfig allows comments but not trailing commas"
            ))
            return issues

        # Check for path aliases
        compiler_options = tsconfig.get("compilerOptions", {})
        paths = compiler_options.get("paths", {})

        if "@/*" not in paths:
            issues.append(ValidationIssue(
                file_path="tsconfig.json",
                line_number=None,
                severity=ValidationSeverity.ERROR,
                code="MISSING_PATH_ALIAS",
                message="tsconfig.json missing @/* path alias",
                suggestion='Add: "paths": { "@/*": ["./src/*"] } in compilerOptions'
            ))

        return issues

    def _validate_file(self, file_path: str, content: str, all_files: Dict[str, str]) -> List[ValidationIssue]:
        """Validate a single source file"""
        issues = []

        # Check for forbidden patterns
        for pattern, code, message, suggestion in self.forbidden_patterns:
            matches = list(re.finditer(pattern, content, re.MULTILINE))
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    code=code,
                    message=message,
                    suggestion=suggestion
                ))

        # Check for React hooks without 'use client'
        if file_path.endswith(('.tsx', '.jsx', '.ts', '.js')):
            hook_issues = self._check_use_client_directive(file_path, content)
            issues.extend(hook_issues)

        # Check for metadata export in 'use client' file
        if "'use client'" in content or '"use client"' in content:
            if re.search(r"export\s+(?:const|let|var)\s+metadata\s*=", content):
                issues.append(ValidationIssue(
                    file_path=file_path,
                    line_number=None,
                    severity=ValidationSeverity.ERROR,
                    code="METADATA_IN_CLIENT",
                    message="Cannot export metadata from a 'use client' file",
                    suggestion="Move metadata export to a Server Component (layout.tsx without 'use client')"
                ))

        # Check CSS files for invalid classes
        if file_path.endswith('.css'):
            css_issues = self._validate_css(file_path, content)
            issues.extend(css_issues)

        return issues

    def _check_use_client_directive(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check if file uses React hooks but is missing 'use client' directive"""
        issues = []

        has_use_client = "'use client'" in content or '"use client"' in content

        # Check for React hooks
        used_hooks = []
        for hook in self.react_hooks:
            # Match hook usage (function call or import)
            if re.search(rf"\b{hook}\s*\(", content) or re.search(rf"import\s*\{{[^}}]*\b{hook}\b[^}}]*\}}", content):
                used_hooks.append(hook)

        # Check for event handlers (onClick, onChange, etc.)
        has_event_handlers = bool(re.search(r"\bon[A-Z][a-zA-Z]+\s*=\s*\{", content))

        # Check for class components (also need 'use client')
        has_class_component = bool(re.search(r"class\s+\w+\s+extends\s+(?:React\.)?Component", content))

        needs_use_client = used_hooks or has_event_handlers or has_class_component

        if needs_use_client and not has_use_client:
            reason = ""
            if used_hooks:
                reason = f"uses React hooks: {', '.join(used_hooks[:3])}"
            elif has_event_handlers:
                reason = "uses event handlers (onClick, onChange, etc.)"
            elif has_class_component:
                reason = "contains a class component"

            issues.append(ValidationIssue(
                file_path=file_path,
                line_number=1,
                severity=ValidationSeverity.ERROR,
                code="MISSING_USE_CLIENT",
                message=f"File {reason} but is missing 'use client' directive",
                suggestion="Add 'use client' as the first line of the file, before any imports"
            ))

        return issues

    def _validate_css(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Validate CSS file for common issues"""
        issues = []

        # Check for @apply with undefined classes
        # This is a simplified check - a full check would need Tailwind config
        apply_matches = re.findall(r"@apply\s+([^;]+);", content)
        for match in apply_matches:
            classes = match.split()
            for cls in classes:
                # Check for common invalid patterns
                if cls in ["border-border", "bg-background", "text-foreground",
                          "bg-muted", "text-muted-foreground", "ring-ring"]:
                    issues.append(ValidationIssue(
                        file_path=file_path,
                        line_number=None,
                        severity=ValidationSeverity.ERROR,
                        code="INVALID_TAILWIND_CLASS",
                        message=f"Class '{cls}' is not defined in Tailwind config",
                        suggestion="Use standard Tailwind classes like bg-white, border-gray-200, etc."
                    ))

        return issues

    def _validate_dependencies(self, files: Dict[str, str]) -> List[ValidationIssue]:
        """Check that all imported packages are in dependencies"""
        issues = []

        if "package.json" not in files:
            return issues

        try:
            pkg = json.loads(files["package.json"])
            deps = set(pkg.get("dependencies", {}).keys())
            dev_deps = set(pkg.get("devDependencies", {}).keys())
            all_deps = deps | dev_deps
        except json.JSONDecodeError:
            return issues

        # Scan all source files for imports
        imported_packages = set()
        for file_path, content in files.items():
            if self._is_source_file(file_path):
                # Find all imports from external packages (not relative paths)
                imports = re.findall(r"(?:import|from)\s+['\"]([^'\"./][^'\"]*)['\"]", content)
                for imp in imports:
                    # Get package name (handle scoped packages like @radix-ui/react-icons)
                    if imp.startswith("@"):
                        parts = imp.split("/")
                        if len(parts) >= 2:
                            package_name = f"{parts[0]}/{parts[1]}"
                        else:
                            package_name = imp
                    else:
                        package_name = imp.split("/")[0]
                    imported_packages.add(package_name)

        # Built-in packages that don't need to be in dependencies
        builtin = {"react", "react-dom", "next", "next/navigation", "next/link", "next/head"}

        for package in imported_packages:
            if package not in all_deps and package not in builtin:
                # Check if it's a subpath of an installed package
                is_subpath = any(package.startswith(f"{dep}/") for dep in all_deps)
                if not is_subpath:
                    issues.append(ValidationIssue(
                        file_path="package.json",
                        line_number=None,
                        severity=ValidationSeverity.ERROR,
                        code="MISSING_DEPENDENCY",
                        message=f"Package '{package}' is imported but not in dependencies",
                        suggestion=f"Add '{package}' to dependencies in package.json"
                    ))

        return issues

    def auto_fix(self, files: Dict[str, str], result: ValidationResult) -> Dict[str, str]:
        """
        Attempt to auto-fix some validation issues.
        Returns modified files dictionary.
        """
        fixed_files = dict(files)

        for issue in result.errors:
            if issue.code == "MISSING_USE_CLIENT":
                # Add 'use client' to the top of the file
                content = fixed_files.get(issue.file_path, "")
                if content and "'use client'" not in content:
                    fixed_files[issue.file_path] = "'use client'\n\n" + content

            elif issue.code == "NEXT_IMAGE_FORBIDDEN":
                # Replace next/image imports with regular img usage
                content = fixed_files.get(issue.file_path, "")
                # Remove the import
                content = re.sub(r"import\s+Image\s+from\s+['\"]next/image['\"];?\n?", "", content)
                # Replace <Image with <img (basic replacement)
                content = re.sub(r"<Image\s+", "<img ", content)
                fixed_files[issue.file_path] = content

            elif issue.code == "WRONG_ROUTER_IMPORT":
                # Fix next/router to next/navigation
                content = fixed_files.get(issue.file_path, "")
                content = content.replace("from 'next/router'", "from 'next/navigation'")
                content = content.replace('from "next/router"', 'from "next/navigation"')
                fixed_files[issue.file_path] = content

        return fixed_files


# Global instance
_validator: Optional[CodeValidator] = None


def get_validator() -> CodeValidator:
    """Get the global validator instance"""
    global _validator
    if _validator is None:
        _validator = CodeValidator()
    return _validator


def validate_files(files: Dict[str, str]) -> ValidationResult:
    """Convenience function to validate files"""
    return get_validator().validate_project(files)


def validate_and_fix(files: Dict[str, str]) -> Tuple[Dict[str, str], ValidationResult]:
    """Validate and auto-fix issues, return fixed files and remaining issues"""
    validator = get_validator()
    result = validator.validate_project(files)

    if not result.is_valid:
        # Attempt auto-fix
        fixed_files = validator.auto_fix(files, result)
        # Re-validate after fixes
        result = validator.validate_project(fixed_files)
        return fixed_files, result

    return files, result
