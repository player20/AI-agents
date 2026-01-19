"""
Domain-Specific Analyzers

Provides specialized analysis for different aspects of a codebase:
- Frontend/UX analysis
- Backend/API analysis
- Architecture analysis

Uses existing AI modules (CodeParser, CodeValidationPipeline) for deep analysis.
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
import re
import logging

from .codebase_analyzer import CodebaseContext, TechStack

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Issue:
    """A code issue found during analysis"""
    severity: str  # "critical", "high", "medium", "low"
    category: str  # "security", "performance", "accessibility", "best_practice"
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
        }


@dataclass
class PatternAnalysis:
    """Analysis of a specific pattern"""
    score: float  # 0-10
    found: bool
    details: str
    issues: List[Issue] = field(default_factory=list)
    positive: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "found": self.found,
            "details": self.details,
            # Return issues as string array for frontend compatibility
            "issues": [i.title if isinstance(i, Issue) else str(i) for i in self.issues],
            "positive": self.positive,
        }


@dataclass
class FrontendAnalysis:
    """Frontend/UX analysis results"""
    score: float  # Overall frontend score 0-10

    # Component analysis
    component_count: int
    component_patterns: List[str]

    # UX patterns
    ux_patterns: Dict[str, PatternAnalysis]

    # State management
    state_management: str
    state_libraries: List[str]

    # Performance
    lazy_loading: PatternAnalysis
    bundle_optimization: PatternAnalysis

    # Issues and metrics
    issues: List[Issue]
    metrics: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "component_count": self.component_count,
            "component_patterns": self.component_patterns,
            "ux_patterns": {k: v.to_dict() for k, v in self.ux_patterns.items()},
            "state_management": self.state_management,
            "state_libraries": self.state_libraries,
            "lazy_loading": self.lazy_loading.to_dict(),
            "bundle_optimization": self.bundle_optimization.to_dict(),
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
        }


@dataclass
class SecurityFinding:
    """Security issue from code scanning"""
    severity: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    rule_id: str = ""
    cwe: Optional[str] = None  # CWE identifier

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "rule_id": self.rule_id,
            "cwe": self.cwe,
        }


@dataclass
class ApiEndpoint:
    """API endpoint information"""
    method: str
    path: str
    file_path: str
    line_number: Optional[int] = None
    has_auth: bool = False
    has_validation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "has_auth": self.has_auth,
            "has_validation": self.has_validation,
        }


@dataclass
class BackendAnalysis:
    """Backend analysis results"""
    score: float  # Overall backend score 0-10

    # API analysis
    endpoints: List[ApiEndpoint]
    api_patterns: List[str]

    # Security
    security_findings: List[SecurityFinding]
    auth_analysis: PatternAnalysis
    input_validation: PatternAnalysis

    # Database
    database_patterns: List[str]
    orm_usage: str

    # Issues and metrics
    issues: List[Issue]
    metrics: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "endpoints": [e.to_dict() for e in self.endpoints],
            "endpoint_count": len(self.endpoints),
            "api_patterns": self.api_patterns,
            "security_findings": [f.to_dict() for f in self.security_findings],
            "auth_analysis": self.auth_analysis.to_dict(),
            "input_validation": self.input_validation.to_dict(),
            "database_patterns": self.database_patterns,
            "orm_usage": self.orm_usage,
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
        }


@dataclass
class DependencyInfo:
    """Dependency/import information"""
    module: str
    imported_by: List[str]
    is_circular: bool = False


@dataclass
class ArchitectureAnalysis:
    """Architecture analysis results"""
    score: float  # Overall architecture score 0-10

    # Structure
    folder_organization: str
    module_boundaries: str

    # Complexity
    total_complexity: int
    avg_complexity: float
    complex_files: List[Dict[str, Any]]

    # Dependencies
    dependency_count: int
    circular_dependencies: List[List[str]]

    # Best practices
    separation_of_concerns: PatternAnalysis
    single_responsibility: PatternAnalysis
    dry_violations: List[Issue]

    # Issues and metrics
    issues: List[Issue]
    metrics: Dict[str, int]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "folder_organization": self.folder_organization,
            "module_boundaries": self.module_boundaries,
            "total_complexity": self.total_complexity,
            "avg_complexity": self.avg_complexity,
            "complex_files": self.complex_files,
            "dependency_count": self.dependency_count,
            "circular_dependencies": self.circular_dependencies,
            "separation_of_concerns": self.separation_of_concerns.to_dict(),
            "single_responsibility": self.single_responsibility.to_dict(),
            "dry_violations": [i.to_dict() for i in self.dry_violations],
            "issues": [i.to_dict() for i in self.issues],
            "metrics": self.metrics,
        }


# =============================================================================
# Frontend Analyzer
# =============================================================================

class FrontendAnalyzer:
    """
    Analyze frontend code for UX patterns, accessibility, and best practices.

    Example:
        analyzer = FrontendAnalyzer()
        result = await analyzer.analyze(files, context)
        print(f"Frontend score: {result.score}")
        print(f"Accessibility: {result.ux_patterns['accessibility'].score}")
    """

    def __init__(self):
        self._parser = None

    def _get_parser(self):
        if self._parser is None:
            try:
                from ..ai.code_parser import CodeParser
                self._parser = CodeParser()
            except ImportError:
                pass
        return self._parser

    async def analyze(
        self,
        files: Dict[str, str],
        context: CodebaseContext
    ) -> FrontendAnalysis:
        """Analyze frontend code"""
        # Filter to frontend files
        frontend_files = self._filter_frontend_files(files)

        # Analyze components
        component_count = self._count_components(frontend_files)
        component_patterns = self._detect_component_patterns(frontend_files)

        # Analyze UX patterns
        ux_patterns = {
            "accessibility": self._check_accessibility(frontend_files),
            "responsive": self._check_responsive(frontend_files),
            "loading_states": self._check_loading_patterns(frontend_files),
            "error_handling": self._check_error_handling(frontend_files),
            "forms": self._check_form_patterns(frontend_files),
        }

        # State management
        state_management, state_libs = self._detect_state_management(frontend_files)

        # Performance
        lazy_loading = self._check_lazy_loading(frontend_files)
        bundle_opt = self._check_bundle_optimization(files)

        # Collect issues
        issues = self._collect_issues(ux_patterns)

        # Calculate score
        score = self._calculate_score(ux_patterns, issues)

        # Metrics
        metrics = {
            "total_files": len(frontend_files),
            "component_files": component_count,
            "css_files": sum(1 for p in frontend_files if p.endswith(('.css', '.scss', '.sass'))),
            "total_lines": sum(c.count('\n') + 1 for c in frontend_files.values()),
        }

        return FrontendAnalysis(
            score=score,
            component_count=component_count,
            component_patterns=component_patterns,
            ux_patterns=ux_patterns,
            state_management=state_management,
            state_libraries=state_libs,
            lazy_loading=lazy_loading,
            bundle_optimization=bundle_opt,
            issues=issues,
            metrics=metrics,
        )

    def _filter_frontend_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Filter to frontend-relevant files"""
        frontend_exts = {'.tsx', '.jsx', '.vue', '.svelte', '.html', '.css', '.scss', '.sass'}
        return {
            p: c for p, c in files.items()
            if Path(p).suffix.lower() in frontend_exts
        }

    def _count_components(self, files: Dict[str, str]) -> int:
        """Count React/Vue components"""
        count = 0
        for path, content in files.items():
            # React function components
            if re.search(r'function\s+[A-Z]\w+\s*\(', content):
                count += 1
            # React arrow function components
            elif re.search(r'const\s+[A-Z]\w+\s*=\s*(?:React\.memo\()?\s*\(?(?:props|\{|[\w,\s]*\))\s*=>', content):
                count += 1
            # Vue SFC
            elif '<template>' in content and '<script' in content:
                count += 1
            # Svelte component
            elif path.endswith('.svelte'):
                count += 1
        return count

    def _detect_component_patterns(self, files: Dict[str, str]) -> List[str]:
        """Detect component organization patterns"""
        patterns = []
        paths = list(files.keys())

        # Check for atomic design
        atomic_dirs = ["atoms", "molecules", "organisms", "templates"]
        if any(d in p.lower() for p in paths for d in atomic_dirs):
            patterns.append("Atomic Design")

        # Check for feature-based
        if any("/features/" in p or "/modules/" in p for p in paths):
            patterns.append("Feature-based")

        # Check for component co-location
        if any(p.endswith('.module.css') or p.endswith('.module.scss') for p in paths):
            patterns.append("CSS Modules")

        # Check for component-per-folder
        component_dirs = sum(1 for p in paths if '/components/' in p and p.count('/') > 2)
        if component_dirs > 5:
            patterns.append("Component-per-folder")

        if not patterns:
            patterns.append("Flat structure")

        return patterns

    def _check_accessibility(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check accessibility patterns"""
        issues = []
        positive = []
        a11y_score = 10.0

        all_content = '\n'.join(files.values())

        for path, content in files.items():
            # Check for missing alt attributes
            img_without_alt = re.findall(r'<img[^>]*(?<!alt=)[^>]*>', content)
            for match in img_without_alt:
                if 'alt=' not in match:
                    issues.append(Issue(
                        severity="medium",
                        category="accessibility",
                        title="Image missing alt attribute",
                        description="Images should have descriptive alt text for screen readers",
                        file_path=path,
                    ))
                    a11y_score -= 0.5

            # Check for onClick without keyboard support
            onclick_no_keyboard = re.findall(r'onClick=[^>]*(?!onKeyDown|onKeyPress|role)', content)
            if onclick_no_keyboard:
                issues.append(Issue(
                    severity="medium",
                    category="accessibility",
                    title="Click handler without keyboard support",
                    description="Interactive elements should support keyboard navigation",
                    file_path=path,
                ))
                a11y_score -= 0.3

        # Positive indicators
        if 'aria-label' in all_content:
            positive.append("ARIA labels used for accessibility")
            a11y_score = min(10, a11y_score + 1)
        if 'role=' in all_content:
            positive.append("ARIA roles defined")
            a11y_score = min(10, a11y_score + 0.5)
        if 'alt=' in all_content:
            positive.append("Alt attributes present on images")
        if 'tabIndex' in all_content or 'tabindex' in all_content:
            positive.append("Tab navigation support")
            a11y_score = min(10, a11y_score + 0.5)

        return PatternAnalysis(
            score=max(0, a11y_score),
            found=bool(issues) or 'aria-' in all_content,
            details=f"Found {len(issues)} accessibility issues",
            issues=issues[:10],
            positive=positive,
        )

    def _check_responsive(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check responsive design patterns"""
        issues = []
        positive = []
        score = 5.0  # Start at middle

        all_content = '\n'.join(files.values())

        # Check for media queries
        media_queries = re.findall(r'@media', all_content)
        if media_queries:
            positive.append(f"Uses {len(media_queries)} media queries")
            score += min(2, len(media_queries) * 0.2)

        # Check for Tailwind responsive classes
        if re.search(r'(sm:|md:|lg:|xl:)', all_content):
            positive.append("Tailwind responsive breakpoints")
            score += 2

        # Check for CSS Grid/Flexbox
        if 'display: grid' in all_content or 'display: flex' in all_content:
            positive.append("CSS Grid/Flexbox layout")
            score += 1

        # Check for viewport meta
        if 'viewport' in all_content:
            positive.append("Viewport meta tag configured")
            score += 0.5

        # Check for fixed widths (bad)
        fixed_widths = re.findall(r'width:\s*\d+px', all_content)
        if len(fixed_widths) > 10:
            issues.append(Issue(
                severity="low",
                category="responsive",
                title="Multiple fixed widths detected",
                description="Consider using relative units for better responsiveness",
            ))
            score -= 1

        return PatternAnalysis(
            score=min(10, max(0, score)),
            found=bool(media_queries) or 'sm:' in all_content,
            details=f"Found {len(media_queries)} media queries",
            issues=issues,
            positive=positive,
        )

    def _check_loading_patterns(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check loading state patterns"""
        issues = []
        positive = []
        score = 5.0

        all_content = '\n'.join(files.values())

        # Check for loading states
        loading_indicators = [
            'isLoading', 'loading', 'Loading', 'Spinner', 'Skeleton',
            'pending', 'isFetching', 'useQuery', 'useSWR',
        ]

        found_patterns = sum(1 for p in loading_indicators if p in all_content)
        if found_patterns > 0:
            positive.append(f"Found {found_patterns} loading state patterns")
        score += min(3, found_patterns * 0.5)

        # Check for Suspense
        if 'Suspense' in all_content:
            positive.append("React Suspense for async loading")
            score += 1

        # Check for error boundaries
        if 'ErrorBoundary' in all_content or 'componentDidCatch' in all_content:
            positive.append("Error boundaries implemented")
            score += 1

        if found_patterns == 0:
            issues.append(Issue(
                severity="medium",
                category="ux",
                title="No loading states detected",
                description="Add loading indicators for async operations",
            ))

        return PatternAnalysis(
            score=min(10, score),
            found=found_patterns > 0,
            details=f"Found {found_patterns} loading patterns",
            issues=issues,
            positive=positive,
        )

    def _check_error_handling(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check error handling in UI"""
        issues = []
        positive = []
        score = 5.0

        all_content = '\n'.join(files.values())

        # Error boundary
        if 'ErrorBoundary' in all_content:
            positive.append("Error boundaries implemented")
            score += 2

        # Error states
        error_patterns = ['error', 'Error', 'isError', 'errorMessage']
        found = sum(1 for p in error_patterns if p in all_content)
        if found > 0:
            positive.append("Error state handling")
        score += min(2, found * 0.5)

        # Try-catch
        if 'try {' in all_content or 'try{' in all_content:
            positive.append("Try-catch blocks for error handling")
            score += 1

        # Toast/notification for errors
        if any(p in all_content for p in ['toast', 'Toast', 'notification', 'Alert']):
            positive.append("Error notifications/toasts")
            score += 1

        return PatternAnalysis(
            score=min(10, score),
            found=found > 0,
            details=f"Found {found} error handling patterns",
            issues=issues,
            positive=positive,
        )

    def _check_form_patterns(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check form handling patterns"""
        issues = []
        positive = []
        score = 5.0

        all_content = '\n'.join(files.values())

        # Form libraries
        form_libs = ['react-hook-form', 'formik', 'useForm', 'Formik']
        if any(lib in all_content for lib in form_libs):
            positive.append("Form library for state management")
            score += 2

        # Validation
        if any(v in all_content for v in ['zod', 'yup', 'joi', 'validate', 'Validation']):
            positive.append("Form validation library")
            score += 2

        # Required fields
        if 'required' in all_content:
            positive.append("Required field validation")
            score += 0.5

        # Controlled inputs
        if 'onChange' in all_content and 'value=' in all_content:
            positive.append("Controlled input components")
            score += 1

        return PatternAnalysis(
            score=min(10, score),
            found='<form' in all_content or 'Form' in all_content,
            details="Form handling analysis",
            issues=issues,
            positive=positive,
        )

    def _detect_state_management(self, files: Dict[str, str]) -> tuple:
        """Detect state management approach"""
        all_content = '\n'.join(files.values())
        libs = []

        state_libs = {
            "Redux": ["redux", "createStore", "useSelector", "useDispatch"],
            "Zustand": ["zustand", "create(", "useStore"],
            "Jotai": ["jotai", "atom(", "useAtom"],
            "Recoil": ["recoil", "RecoilRoot", "useRecoilState"],
            "MobX": ["mobx", "observable", "makeObservable"],
            "Context API": ["createContext", "useContext", "Provider"],
            "React Query": ["useQuery", "useMutation", "@tanstack/react-query"],
            "SWR": ["useSWR", "swr"],
        }

        for lib, patterns in state_libs.items():
            if any(p in all_content for p in patterns):
                libs.append(lib)

        if not libs:
            return "Local state (useState)", []

        return libs[0], libs

    def _check_lazy_loading(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check lazy loading implementation"""
        all_content = '\n'.join(files.values())
        score = 5.0
        issues = []
        positive = []

        # React.lazy
        if 'React.lazy' in all_content or 'lazy(' in all_content:
            positive.append("React.lazy for code splitting")
            score += 2

        # Dynamic imports
        if 'import(' in all_content:
            positive.append("Dynamic imports")
            score += 2

        # Image lazy loading
        if 'loading="lazy"' in all_content:
            positive.append("Lazy loading images")
            score += 1

        # Next.js dynamic
        if 'next/dynamic' in all_content:
            positive.append("Next.js dynamic imports")
            score += 2

        return PatternAnalysis(
            score=min(10, score),
            found='lazy' in all_content.lower(),
            details="Lazy loading implementation",
            issues=issues,
            positive=positive,
        )

    def _check_bundle_optimization(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check bundle optimization"""
        all_content = '\n'.join(files.values())
        paths = list(files.keys())
        score = 5.0
        issues = []
        positive = []

        # Tree shaking imports
        named_imports = re.findall(r'import\s*\{[^}]+\}\s*from', all_content)
        if named_imports:
            positive.append(f"{len(named_imports)} tree-shakeable imports")
            score += 1

        # Code splitting config
        if any('splitChunks' in c for c in files.values()):
            positive.append("Webpack chunk splitting configured")
            score += 2

        # Bundle analyzer
        if 'bundle-analyzer' in all_content:
            positive.append("Bundle analyzer configured")
            score += 1

        return PatternAnalysis(
            score=min(10, score),
            found=bool(named_imports),
            details=f"Found {len(named_imports)} tree-shakeable imports",
            issues=issues,
            positive=positive,
        )

    def _collect_issues(self, ux_patterns: Dict[str, PatternAnalysis]) -> List[Issue]:
        """Collect all issues from patterns"""
        issues = []
        for pattern in ux_patterns.values():
            issues.extend(pattern.issues)
        return issues

    def _calculate_score(
        self,
        ux_patterns: Dict[str, PatternAnalysis],
        issues: List[Issue]
    ) -> float:
        """Calculate overall frontend score"""
        pattern_scores = [p.score for p in ux_patterns.values()]
        avg_score = sum(pattern_scores) / len(pattern_scores) if pattern_scores else 5.0

        # Deduct for critical issues
        critical = sum(1 for i in issues if i.severity == "critical")
        high = sum(1 for i in issues if i.severity == "high")

        score = avg_score - (critical * 1.0) - (high * 0.5)
        return max(0, min(10, score))


# =============================================================================
# Backend Analyzer
# =============================================================================

class BackendAnalyzer:
    """
    Analyze backend code for security, API design, and best practices.
    """

    def __init__(self):
        self._validation_pipeline = None

    def _get_validation_pipeline(self):
        if self._validation_pipeline is None:
            try:
                from ..ai.code_validation import CodeValidationPipeline
                self._validation_pipeline = CodeValidationPipeline()
            except ImportError:
                logger.warning("CodeValidationPipeline not available")
        return self._validation_pipeline

    async def analyze(
        self,
        files: Dict[str, str],
        context: CodebaseContext
    ) -> BackendAnalysis:
        """Analyze backend code"""
        # Filter to backend files
        backend_files = self._filter_backend_files(files)

        # Extract API endpoints
        endpoints = self._extract_endpoints(backend_files)

        # Detect API patterns
        api_patterns = self._detect_api_patterns(backend_files)

        # Security analysis
        security_findings = await self._run_security_scan(backend_files)

        # Auth analysis
        auth_analysis = self._analyze_auth(backend_files)

        # Input validation analysis
        input_validation = self._analyze_input_validation(backend_files)

        # Database patterns
        db_patterns, orm = self._analyze_database(backend_files)

        # Collect issues
        issues = self._collect_backend_issues(
            endpoints, security_findings, auth_analysis, input_validation
        )

        # Calculate score
        score = self._calculate_score(security_findings, auth_analysis, input_validation)

        # Metrics
        metrics = {
            "total_files": len(backend_files),
            "endpoints": len(endpoints),
            "security_issues": len(security_findings),
            "total_lines": sum(c.count('\n') + 1 for c in backend_files.values()),
        }

        return BackendAnalysis(
            score=score,
            endpoints=endpoints,
            api_patterns=api_patterns,
            security_findings=security_findings,
            auth_analysis=auth_analysis,
            input_validation=input_validation,
            database_patterns=db_patterns,
            orm_usage=orm,
            issues=issues,
            metrics=metrics,
        )

    def _filter_backend_files(self, files: Dict[str, str]) -> Dict[str, str]:
        """Filter to backend-relevant files"""
        backend_exts = {'.py', '.ts', '.js', '.go', '.java', '.rb', '.php', '.rs'}
        exclude_patterns = ['test', 'spec', '.d.ts', 'mock']

        return {
            p: c for p, c in files.items()
            if Path(p).suffix.lower() in backend_exts
            and not any(excl in p.lower() for excl in exclude_patterns)
        }

    def _extract_endpoints(self, files: Dict[str, str]) -> List[ApiEndpoint]:
        """Extract API endpoints from code"""
        endpoints = []

        # FastAPI patterns
        fastapi_pattern = r'@(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'

        # Express patterns
        express_pattern = r'(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'

        # Flask patterns
        flask_pattern = r'@(?:app|bp)\.route\s*\(\s*["\']([^"\']+)["\'][^)]*methods\s*=\s*\[([^\]]+)\]'

        # Django patterns
        django_pattern = r'path\s*\(\s*["\']([^"\']+)["\']'

        for path, content in files.items():
            lines = content.split('\n')

            for i, line in enumerate(lines):
                # FastAPI/Express
                for match in re.finditer(fastapi_pattern, line, re.IGNORECASE):
                    method, route = match.groups()
                    endpoints.append(ApiEndpoint(
                        method=method.upper(),
                        path=route,
                        file_path=path,
                        line_number=i + 1,
                        has_auth=self._check_endpoint_auth(lines, i),
                        has_validation=self._check_endpoint_validation(lines, i),
                    ))

                for match in re.finditer(express_pattern, line, re.IGNORECASE):
                    method, route = match.groups()
                    endpoints.append(ApiEndpoint(
                        method=method.upper(),
                        path=route,
                        file_path=path,
                        line_number=i + 1,
                        has_auth='auth' in '\n'.join(lines[max(0, i-5):i+5]).lower(),
                    ))

        return endpoints

    def _check_endpoint_auth(self, lines: List[str], line_idx: int) -> bool:
        """Check if endpoint has authentication"""
        context = '\n'.join(lines[max(0, line_idx-5):line_idx+3])
        auth_indicators = ['Depends', 'auth', 'Auth', 'jwt', 'token', 'Bearer', 'middleware']
        return any(ind in context for ind in auth_indicators)

    def _check_endpoint_validation(self, lines: List[str], line_idx: int) -> bool:
        """Check if endpoint has input validation"""
        context = '\n'.join(lines[max(0, line_idx-3):line_idx+10])
        validation_indicators = ['BaseModel', 'Schema', 'validate', 'zod', 'joi', 'Pydantic']
        return any(ind in context for ind in validation_indicators)

    def _detect_api_patterns(self, files: Dict[str, str]) -> List[str]:
        """Detect API design patterns"""
        patterns = []
        all_content = '\n'.join(files.values())

        if 'GraphQL' in all_content or 'graphql' in all_content:
            patterns.append("GraphQL")
        if '@app.' in all_content or 'router.' in all_content:
            patterns.append("REST")
        if 'grpc' in all_content.lower():
            patterns.append("gRPC")
        if 'websocket' in all_content.lower():
            patterns.append("WebSocket")

        if not patterns:
            patterns.append("REST")

        return patterns

    async def _run_security_scan(self, files: Dict[str, str]) -> List[SecurityFinding]:
        """Run security scan using CodeValidationPipeline"""
        findings = []
        pipeline = self._get_validation_pipeline()

        if pipeline is None:
            # Fallback to basic pattern matching
            return self._basic_security_scan(files)

        for path, content in files.items():
            # Determine language
            ext = Path(path).suffix.lower()
            lang_map = {'.py': 'python', '.ts': 'typescript', '.js': 'javascript'}
            language = lang_map.get(ext)

            if language:
                try:
                    result = pipeline.validate(content, language, security_scan=True)
                    for issue in result.issues:
                        if issue.category.value == 'security':
                            findings.append(SecurityFinding(
                                severity=issue.severity.value,
                                title=issue.message[:100],
                                description=issue.message,
                                file_path=path,
                                line_number=issue.line,
                                rule_id=issue.code,
                            ))
                except Exception as e:
                    logger.warning(f"Security scan failed for {path}: {e}")

        return findings

    def _basic_security_scan(self, files: Dict[str, str]) -> List[SecurityFinding]:
        """Basic pattern-based security scan"""
        findings = []

        # Dangerous patterns
        dangerous_patterns = [
            (r'eval\s*\(', "Potential code injection via eval()", "high"),
            (r'exec\s*\(', "Potential code injection via exec()", "high"),
            (r'subprocess\..*shell\s*=\s*True', "Shell injection risk", "high"),
            (r'os\.system\s*\(', "Command injection risk", "medium"),
            (r'pickle\.loads?\s*\(', "Insecure deserialization", "high"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password", "critical"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key", "critical"),
            (r'\.execute\s*\([^)]*\+', "Potential SQL injection", "high"),
            (r'innerHTML\s*=', "Potential XSS via innerHTML", "medium"),
            (r'dangerouslySetInnerHTML', "React XSS risk", "medium"),
        ]

        for path, content in files.items():
            for pattern, desc, severity in dangerous_patterns:
                matches = list(re.finditer(pattern, content, re.IGNORECASE))
                for match in matches[:3]:  # Limit per pattern
                    line_num = content[:match.start()].count('\n') + 1
                    findings.append(SecurityFinding(
                        severity=severity,
                        title=desc,
                        description=f"Pattern '{pattern}' found",
                        file_path=path,
                        line_number=line_num,
                    ))

        return findings

    def _analyze_auth(self, files: Dict[str, str]) -> PatternAnalysis:
        """Analyze authentication implementation"""
        all_content = '\n'.join(files.values())
        score = 5.0
        issues = []

        # Check for auth mechanisms
        auth_mechanisms = {
            "JWT": ["jwt", "jsonwebtoken", "jose", "python-jose"],
            "OAuth": ["oauth", "passport", "authlib"],
            "Session": ["session", "cookie", "express-session"],
            "API Key": ["api_key", "apikey", "x-api-key"],
        }

        found_mechanisms = []
        for mech, patterns in auth_mechanisms.items():
            if any(p in all_content.lower() for p in patterns):
                found_mechanisms.append(mech)
                score += 1

        # Check for secure practices
        if 'bcrypt' in all_content.lower() or 'argon2' in all_content.lower():
            score += 1
        if 'https' in all_content.lower():
            score += 0.5

        # Check for auth on routes
        if 'Depends(' in all_content or 'middleware' in all_content.lower():
            score += 1

        if not found_mechanisms:
            issues.append(Issue(
                severity="high",
                category="security",
                title="No authentication mechanism detected",
                description="Consider implementing authentication for protected endpoints",
            ))

        return PatternAnalysis(
            score=min(10, score),
            found=bool(found_mechanisms),
            details=f"Found: {', '.join(found_mechanisms) if found_mechanisms else 'None'}",
            issues=issues,
        )

    def _analyze_input_validation(self, files: Dict[str, str]) -> PatternAnalysis:
        """Analyze input validation practices"""
        all_content = '\n'.join(files.values())
        score = 5.0
        issues = []

        # Validation libraries
        validation_libs = ['pydantic', 'zod', 'joi', 'yup', 'marshmallow', 'cerberus']
        found_libs = [lib for lib in validation_libs if lib in all_content.lower()]

        if found_libs:
            score += 2

        # Type hints (Python)
        if ': str' in all_content or ': int' in all_content:
            score += 1

        # Schema validation
        if 'Schema' in all_content or 'BaseModel' in all_content:
            score += 1

        # Input sanitization
        if 'sanitize' in all_content.lower() or 'escape' in all_content.lower():
            score += 1

        if not found_libs:
            issues.append(Issue(
                severity="medium",
                category="security",
                title="No validation library detected",
                description="Use a validation library like Pydantic, Zod, or Joi for input validation",
            ))

        return PatternAnalysis(
            score=min(10, score),
            found=bool(found_libs),
            details=f"Validation: {', '.join(found_libs) if found_libs else 'Basic'}",
            issues=issues,
        )

    def _analyze_database(self, files: Dict[str, str]) -> tuple:
        """Analyze database access patterns"""
        all_content = '\n'.join(files.values())
        patterns = []
        orm = "None detected"

        orms = {
            "Prisma": ["prisma", "@prisma/client", "PrismaClient"],
            "SQLAlchemy": ["sqlalchemy", "from sqlalchemy"],
            "TypeORM": ["typeorm", "@Entity", "Repository"],
            "Drizzle": ["drizzle-orm"],
            "Sequelize": ["sequelize", "Sequelize"],
            "Mongoose": ["mongoose", "Schema("],
            "Django ORM": ["models.Model", "django.db"],
        }

        for orm_name, indicators in orms.items():
            if any(ind in all_content for ind in indicators):
                orm = orm_name
                patterns.append(f"ORM: {orm_name}")
                break

        # Check for raw SQL (risky)
        if re.search(r'\.execute\s*\(["\'][^"\']*SELECT', all_content):
            patterns.append("Raw SQL queries")

        # Check for parameterized queries
        if re.search(r'\.execute\s*\([^)]*,\s*\(', all_content):
            patterns.append("Parameterized queries")

        return patterns, orm

    def _collect_backend_issues(
        self,
        endpoints: List[ApiEndpoint],
        security: List[SecurityFinding],
        auth: PatternAnalysis,
        validation: PatternAnalysis
    ) -> List[Issue]:
        """Collect all backend issues"""
        issues = []

        # Security findings
        for finding in security:
            issues.append(Issue(
                severity=finding.severity,
                category="security",
                title=finding.title,
                description=finding.description,
                file_path=finding.file_path,
                line_number=finding.line_number,
            ))

        # Auth issues
        issues.extend(auth.issues)

        # Validation issues
        issues.extend(validation.issues)

        # Endpoint issues
        unprotected = [e for e in endpoints if not e.has_auth and e.method in ['POST', 'PUT', 'DELETE']]
        if unprotected:
            issues.append(Issue(
                severity="high",
                category="security",
                title=f"{len(unprotected)} endpoints without authentication",
                description="POST/PUT/DELETE endpoints should require authentication",
            ))

        return issues

    def _calculate_score(
        self,
        security: List[SecurityFinding],
        auth: PatternAnalysis,
        validation: PatternAnalysis
    ) -> float:
        """Calculate overall backend score"""
        base = (auth.score + validation.score) / 2

        # Deduct for security issues
        critical = sum(1 for f in security if f.severity == "critical")
        high = sum(1 for f in security if f.severity == "high")

        score = base - (critical * 2) - (high * 0.5)
        return max(0, min(10, score))


# =============================================================================
# Architecture Analyzer
# =============================================================================

class ArchitectureAnalyzer:
    """
    Analyze codebase architecture, complexity, and organization.
    """

    def __init__(self):
        self._parser = None

    def _get_parser(self):
        if self._parser is None:
            try:
                from ..ai.code_parser import CodeParser
                self._parser = CodeParser()
            except ImportError:
                pass
        return self._parser

    async def analyze(
        self,
        files: Dict[str, str],
        context: CodebaseContext
    ) -> ArchitectureAnalysis:
        """Analyze architecture"""
        # Analyze folder organization
        folder_org = self._analyze_folder_organization(files)
        module_boundaries = self._analyze_module_boundaries(files)

        # Complexity analysis
        total_complexity, avg_complexity, complex_files = self._analyze_complexity(files)

        # Dependency analysis
        dep_count, circular_deps = self._analyze_dependencies(files)

        # Best practices
        separation = self._check_separation_of_concerns(files, context)
        srp = self._check_single_responsibility(files)
        dry_violations = self._find_dry_violations(files)

        # Collect issues
        issues = self._collect_arch_issues(
            complex_files, circular_deps, separation, srp, dry_violations
        )

        # Calculate score
        score = self._calculate_score(
            complex_files, circular_deps, separation, srp, issues
        )

        # Metrics
        metrics = {
            "total_files": len(files),
            "total_complexity": total_complexity,
            "avg_complexity": round(avg_complexity, 2),
            "dependencies": dep_count,
            "circular_deps": len(circular_deps),
        }

        return ArchitectureAnalysis(
            score=score,
            folder_organization=folder_org,
            module_boundaries=module_boundaries,
            total_complexity=total_complexity,
            avg_complexity=avg_complexity,
            complex_files=complex_files,
            dependency_count=dep_count,
            circular_dependencies=circular_deps,
            separation_of_concerns=separation,
            single_responsibility=srp,
            dry_violations=dry_violations,
            issues=issues,
            metrics=metrics,
        )

    def _analyze_folder_organization(self, files: Dict[str, str]) -> str:
        """Describe folder organization pattern"""
        paths = list(files.keys())

        if any("features/" in p or "modules/" in p for p in paths):
            return "Feature-based organization"
        if any("domain/" in p for p in paths):
            return "Domain-driven organization"
        if any("layers/" in p for p in paths):
            return "Layered architecture"
        if any("/controllers/" in p and "/models/" in p for p in paths):
            return "MVC pattern"
        if any("/src/" in p for p in paths):
            return "Standard src layout"

        return "Flat organization"

    def _analyze_module_boundaries(self, files: Dict[str, str]) -> str:
        """Analyze how well modules are separated"""
        paths = list(files.keys())

        # Check for clear boundaries
        has_index = sum(1 for p in paths if 'index.' in p)
        has_barrel = sum(1 for p in paths if '__init__.py' in p)

        if has_index > 5 or has_barrel > 5:
            return "Clear module boundaries with barrel exports"
        if any('/api/' in p and '/ui/' in p for p in paths):
            return "Separated by concern"

        return "Implicit module boundaries"

    def _analyze_complexity(self, files: Dict[str, str]) -> tuple:
        """Analyze code complexity"""
        parser = self._get_parser()
        complexities = []
        complex_files = []

        for path, content in files.items():
            # Calculate cyclomatic complexity heuristically
            complexity = 1

            # Count decision points
            for keyword in ['if ', 'elif ', 'else if ', 'for ', 'while ', 'case ',
                          'catch ', 'except ', ' && ', ' || ', ' and ', ' or ', ' ? ']:
                complexity += content.count(keyword)

            complexities.append(complexity)

            # Flag complex files
            if complexity > 50:
                complex_files.append({
                    "path": path,
                    "complexity": complexity,
                    "lines": content.count('\n') + 1,
                })

        total = sum(complexities)
        avg = total / len(complexities) if complexities else 0

        # Sort by complexity
        complex_files.sort(key=lambda x: x['complexity'], reverse=True)

        return total, avg, complex_files[:10]  # Top 10

    def _analyze_dependencies(self, files: Dict[str, str]) -> tuple:
        """Analyze import dependencies"""
        imports: Dict[str, Set[str]] = {}

        for path, content in files.items():
            imports[path] = set()

            # Python imports
            for match in re.finditer(r'^(?:from\s+(\S+)|import\s+(\S+))', content, re.MULTILINE):
                module = match.group(1) or match.group(2)
                if module:
                    imports[path].add(module.split('.')[0])

            # JS/TS imports
            for match in re.finditer(r'import\s+.*from\s+["\']([^"\']+)["\']', content):
                module = match.group(1)
                if module.startswith('.'):
                    imports[path].add(module)

        # Find circular dependencies
        circular = self._find_circular_deps(imports)

        return sum(len(i) for i in imports.values()), circular

    def _find_circular_deps(self, imports: Dict[str, Set[str]]) -> List[List[str]]:
        """Find circular dependency chains"""
        circular = []

        for file, deps in imports.items():
            for dep in deps:
                # Check if dep imports file
                dep_deps = imports.get(dep, set())
                if file in dep_deps or Path(file).stem in dep_deps:
                    if [file, dep] not in circular and [dep, file] not in circular:
                        circular.append([file, dep])

        return circular[:5]  # Limit

    def _check_separation_of_concerns(
        self,
        files: Dict[str, str],
        context: CodebaseContext
    ) -> PatternAnalysis:
        """Check separation of concerns"""
        score = 5.0
        issues = []
        paths = list(files.keys())

        # Check for UI/logic separation
        has_ui_folder = any('/components/' in p or '/views/' in p for p in paths)
        has_logic_folder = any('/services/' in p or '/lib/' in p or '/utils/' in p for p in paths)

        if has_ui_folder and has_logic_folder:
            score += 2

        # Check for data/logic separation
        has_data_folder = any('/models/' in p or '/schemas/' in p for p in paths)
        if has_data_folder:
            score += 1

        # Check for mixed concerns
        for path, content in files.items():
            if '/components/' in path and 'fetch(' in content:
                issues.append(Issue(
                    severity="medium",
                    category="architecture",
                    title="Data fetching in component",
                    description="Consider moving data fetching to a service layer",
                    file_path=path,
                ))
                score -= 0.5

        return PatternAnalysis(
            score=min(10, max(0, score)),
            found=has_ui_folder or has_logic_folder,
            details="Separation analysis",
            issues=issues,
        )

    def _check_single_responsibility(self, files: Dict[str, str]) -> PatternAnalysis:
        """Check single responsibility principle"""
        score = 7.0
        issues = []

        for path, content in files.items():
            lines = content.count('\n') + 1

            # Very large files
            if lines > 500:
                issues.append(Issue(
                    severity="medium",
                    category="architecture",
                    title=f"Large file: {lines} lines",
                    description="Consider splitting into smaller, focused modules",
                    file_path=path,
                ))
                score -= 0.5

            # Many classes in one file
            class_count = len(re.findall(r'^class\s+\w+', content, re.MULTILINE))
            if class_count > 3:
                issues.append(Issue(
                    severity="low",
                    category="architecture",
                    title=f"Multiple classes ({class_count}) in one file",
                    description="Consider one class per file",
                    file_path=path,
                ))
                score -= 0.3

        return PatternAnalysis(
            score=max(0, min(10, score)),
            found=True,
            details=f"Found {len(issues)} SRP violations",
            issues=issues,
        )

    def _find_dry_violations(self, files: Dict[str, str]) -> List[Issue]:
        """Find DRY (Don't Repeat Yourself) violations"""
        issues = []

        # Simple: find duplicate function signatures
        function_sigs = []
        for path, content in files.items():
            for match in re.finditer(r'(?:function|def|const)\s+(\w+)\s*\([^)]*\)', content):
                func_name = match.group(1)
                if func_name not in ['constructor', 'init', '__init__']:
                    function_sigs.append((func_name, path))

        # Find duplicates
        seen = {}
        for name, path in function_sigs:
            if name in seen:
                if seen[name] != path:  # Different files
                    issues.append(Issue(
                        severity="low",
                        category="architecture",
                        title=f"Duplicate function name: {name}",
                        description=f"Found in {path} and {seen[name]}. Consider sharing code.",
                        file_path=path,
                    ))
            else:
                seen[name] = path

        return issues[:10]  # Limit

    def _collect_arch_issues(
        self,
        complex_files: List[Dict],
        circular: List[List[str]],
        separation: PatternAnalysis,
        srp: PatternAnalysis,
        dry: List[Issue]
    ) -> List[Issue]:
        """Collect all architecture issues"""
        issues = []

        # Complexity issues
        for cf in complex_files[:5]:
            if cf['complexity'] > 100:
                issues.append(Issue(
                    severity="high",
                    category="architecture",
                    title=f"Very high complexity: {cf['complexity']}",
                    description="Refactor to reduce cyclomatic complexity",
                    file_path=cf['path'],
                ))

        # Circular dependency issues
        for cycle in circular:
            issues.append(Issue(
                severity="medium",
                category="architecture",
                title="Circular dependency detected",
                description=f"Cycle: {' -> '.join(cycle)}",
            ))

        issues.extend(separation.issues)
        issues.extend(srp.issues)
        issues.extend(dry)

        return issues

    def _calculate_score(
        self,
        complex_files: List[Dict],
        circular: List[List[str]],
        separation: PatternAnalysis,
        srp: PatternAnalysis,
        issues: List[Issue]
    ) -> float:
        """Calculate architecture score"""
        base = (separation.score + srp.score) / 2

        # Deduct for complexity
        very_complex = sum(1 for cf in complex_files if cf['complexity'] > 100)
        base -= very_complex * 0.5

        # Deduct for circular deps
        base -= len(circular) * 0.5

        return max(0, min(10, base))
