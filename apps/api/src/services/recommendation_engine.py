"""
Recommendation Engine

Generates context-aware recommendations based on code analysis.
Uses LLM for intelligent suggestions when available, with rule-based fallback.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

from .codebase_analyzer import CodebaseContext, PlatformType
from .domain_analyzers import (
    FrontendAnalysis, BackendAnalysis, ArchitectureAnalysis,
    Issue, SecurityFinding
)

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """A specific, actionable recommendation"""
    priority: str          # "critical", "high", "medium", "low"
    category: str          # "security", "ux", "performance", "architecture", "maintainability"
    title: str
    description: str
    impact: str            # Why this matters
    effort: str            # "low", "medium", "high"
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    current_code: Optional[str] = None
    suggested_code: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "priority": self.priority,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "impact": self.impact,
            "effort": self.effort,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "current_code": self.current_code,
            "suggested_code": self.suggested_code,
        }


class RecommendationEngine:
    """
    Generate context-aware recommendations based on code analysis.

    Example:
        engine = RecommendationEngine()
        recs = await engine.generate_recommendations(
            context, frontend, backend, architecture
        )
        for rec in recs:
            print(f"[{rec.priority}] {rec.title}")
    """

    def __init__(self):
        self._llm_router = None

    def _get_llm_router(self):
        """Lazy load LLM router"""
        if self._llm_router is None:
            try:
                from ..llm.router import get_llm_router
                self._llm_router = get_llm_router()
            except ImportError:
                logger.warning("LLM router not available")
        return self._llm_router

    async def generate_recommendations(
        self,
        context: CodebaseContext,
        frontend: Optional[FrontendAnalysis],
        backend: Optional[BackendAnalysis],
        architecture: Optional[ArchitectureAnalysis]
    ) -> List[Recommendation]:
        """
        Generate recommendations based on all analysis results.

        Args:
            context: Codebase context
            frontend: Frontend analysis results
            backend: Backend analysis results
            architecture: Architecture analysis results

        Returns:
            List of prioritized recommendations
        """
        recommendations = []

        # Generate recommendations from each domain
        if backend:
            recommendations.extend(self._security_recommendations(backend, context))
            recommendations.extend(self._backend_recommendations(backend, context))

        if frontend:
            recommendations.extend(self._frontend_recommendations(frontend, context))

        if architecture:
            recommendations.extend(self._architecture_recommendations(architecture, context))

        # Add framework-specific recommendations
        recommendations.extend(self._framework_recommendations(context))

        # Try LLM-enhanced recommendations
        llm_recs = await self._generate_llm_recommendations(
            context, frontend, backend, architecture
        )
        recommendations.extend(llm_recs)

        # Deduplicate and prioritize
        recommendations = self._deduplicate(recommendations)
        recommendations = self._prioritize(recommendations)

        return recommendations[:15]  # Top 15

    def _security_recommendations(
        self,
        backend: BackendAnalysis,
        context: CodebaseContext
    ) -> List[Recommendation]:
        """Generate security recommendations"""
        recs = []

        # Critical security findings
        for finding in backend.security_findings:
            if finding.severity in ["critical", "high"]:
                recs.append(Recommendation(
                    priority=finding.severity,
                    category="security",
                    title=f"Fix: {finding.title}",
                    description=finding.description,
                    impact="Security vulnerability that could be exploited",
                    effort="medium",
                    file_path=finding.file_path,
                    line_number=finding.line_number,
                ))

        # Auth recommendations
        if backend.auth_analysis.score < 6:
            if not backend.auth_analysis.found:
                recs.append(Recommendation(
                    priority="high",
                    category="security",
                    title="Implement authentication",
                    description="No authentication mechanism detected. Add JWT, OAuth, or session-based auth.",
                    impact="Unauthorized access to protected resources",
                    effort="high",
                    suggested_code=self._get_auth_example(context.tech_stack.frameworks),
                ))

        # Input validation
        if backend.input_validation.score < 6:
            recs.append(Recommendation(
                priority="high",
                category="security",
                title="Add input validation",
                description="Implement schema validation for all API inputs using Pydantic, Zod, or similar.",
                impact="Prevents injection attacks and data corruption",
                effort="medium",
                suggested_code=self._get_validation_example(context.tech_stack.frameworks),
            ))

        # Unprotected endpoints
        unprotected = [e for e in backend.endpoints if not e.has_auth and e.method in ['POST', 'PUT', 'DELETE']]
        if unprotected:
            recs.append(Recommendation(
                priority="high",
                category="security",
                title=f"Protect {len(unprotected)} write endpoints",
                description=f"Endpoints like {unprotected[0].method} {unprotected[0].path} lack authentication",
                impact="Unauthorized data modification",
                effort="medium",
                file_path=unprotected[0].file_path,
                line_number=unprotected[0].line_number,
            ))

        return recs

    def _backend_recommendations(
        self,
        backend: BackendAnalysis,
        context: CodebaseContext
    ) -> List[Recommendation]:
        """Generate backend recommendations"""
        recs = []

        # ORM usage
        if backend.orm_usage == "None detected" and "Raw SQL" in backend.database_patterns:
            recs.append(Recommendation(
                priority="medium",
                category="maintainability",
                title="Consider using an ORM",
                description="Raw SQL queries detected. An ORM like Prisma, SQLAlchemy, or TypeORM improves maintainability.",
                impact="Reduces SQL injection risk and improves code clarity",
                effort="high",
            ))

        # API documentation
        if len(backend.endpoints) > 10:
            recs.append(Recommendation(
                priority="low",
                category="maintainability",
                title="Add OpenAPI documentation",
                description=f"With {len(backend.endpoints)} endpoints, API documentation becomes essential.",
                impact="Improves developer experience and API adoption",
                effort="low",
            ))

        return recs

    def _frontend_recommendations(
        self,
        frontend: FrontendAnalysis,
        context: CodebaseContext
    ) -> List[Recommendation]:
        """Generate frontend recommendations"""
        recs = []

        # Accessibility
        a11y = frontend.ux_patterns.get("accessibility")
        if a11y and a11y.score < 7:
            for issue in a11y.issues[:2]:
                recs.append(Recommendation(
                    priority="medium",
                    category="ux",
                    title=issue.title,
                    description=issue.description,
                    impact="Improves accessibility for users with disabilities",
                    effort="low",
                    file_path=issue.file_path,
                ))

        # Loading states
        loading = frontend.ux_patterns.get("loading_states")
        if loading and loading.score < 5:
            recs.append(Recommendation(
                priority="medium",
                category="ux",
                title="Add loading indicators",
                description="Implement loading states for async operations (Suspense, skeletons, spinners)",
                impact="Improves perceived performance and user experience",
                effort="low",
                suggested_code=self._get_loading_example(context.tech_stack.frameworks),
            ))

        # Error handling
        errors = frontend.ux_patterns.get("error_handling")
        if errors and errors.score < 5:
            recs.append(Recommendation(
                priority="medium",
                category="ux",
                title="Improve error handling",
                description="Add error boundaries and user-friendly error messages",
                impact="Prevents white screens and improves error recovery",
                effort="medium",
            ))

        # Lazy loading
        if frontend.lazy_loading.score < 6:
            recs.append(Recommendation(
                priority="low",
                category="performance",
                title="Implement lazy loading",
                description="Use React.lazy/dynamic imports for code splitting",
                impact="Reduces initial bundle size and improves load time",
                effort="low",
            ))

        # State management
        if frontend.state_management == "Local state (useState)" and frontend.component_count > 20:
            recs.append(Recommendation(
                priority="low",
                category="architecture",
                title="Consider state management library",
                description="With many components, consider Zustand, Jotai, or React Query for better state management",
                impact="Reduces prop drilling and improves data flow",
                effort="medium",
            ))

        return recs

    def _architecture_recommendations(
        self,
        architecture: ArchitectureAnalysis,
        context: CodebaseContext
    ) -> List[Recommendation]:
        """Generate architecture recommendations"""
        recs = []

        # High complexity
        for cf in architecture.complex_files[:3]:
            if cf['complexity'] > 75:
                recs.append(Recommendation(
                    priority="medium",
                    category="maintainability",
                    title=f"Refactor complex file",
                    description=f"Cyclomatic complexity of {cf['complexity']} is too high. Consider breaking into smaller functions.",
                    impact="Improves testability and reduces bugs",
                    effort="medium",
                    file_path=cf['path'],
                ))

        # Circular dependencies
        for cycle in architecture.circular_dependencies[:2]:
            recs.append(Recommendation(
                priority="medium",
                category="architecture",
                title="Remove circular dependency",
                description=f"Circular import between {' and '.join(cycle)}",
                impact="Prevents runtime errors and improves build times",
                effort="medium",
            ))

        # Separation of concerns
        if architecture.separation_of_concerns.score < 6:
            recs.append(Recommendation(
                priority="medium",
                category="architecture",
                title="Improve separation of concerns",
                description="Separate UI components from business logic and data fetching",
                impact="Improves testability and code reuse",
                effort="high",
            ))

        # Large files
        srp_issues = [i for i in architecture.single_responsibility.issues if "Large file" in i.title]
        if srp_issues:
            largest = srp_issues[0]
            recs.append(Recommendation(
                priority="low",
                category="maintainability",
                title="Split large files",
                description=largest.description,
                impact="Improves navigation and maintenance",
                effort="medium",
                file_path=largest.file_path,
            ))

        return recs

    def _framework_recommendations(self, context: CodebaseContext) -> List[Recommendation]:
        """Generate framework-specific recommendations"""
        recs = []
        frameworks = context.tech_stack.frameworks

        # Next.js specific
        if "Next.js" in frameworks:
            if "Image" not in str(context):
                recs.append(Recommendation(
                    priority="low",
                    category="performance",
                    title="Use next/image for images",
                    description="Next.js Image component provides automatic optimization",
                    impact="Reduces image payload and improves Core Web Vitals",
                    effort="low",
                ))

        # React specific
        if "React" in frameworks:
            recs.append(Recommendation(
                priority="low",
                category="performance",
                title="Review memo/useMemo usage",
                description="Ensure expensive computations are memoized appropriately",
                impact="Prevents unnecessary re-renders",
                effort="low",
            ))

        # FastAPI specific
        if "FastAPI" in frameworks:
            recs.append(Recommendation(
                priority="low",
                category="maintainability",
                title="Use dependency injection",
                description="Leverage FastAPI's Depends() for database connections and services",
                impact="Improves testability and code organization",
                effort="low",
            ))

        return recs

    async def _generate_llm_recommendations(
        self,
        context: CodebaseContext,
        frontend: Optional[FrontendAnalysis],
        backend: Optional[BackendAnalysis],
        architecture: Optional[ArchitectureAnalysis]
    ) -> List[Recommendation]:
        """Generate recommendations using LLM for deeper insights"""
        router = self._get_llm_router()

        if router is None:
            return []

        try:
            # Build prompt with analysis summary
            prompt = self._build_llm_prompt(context, frontend, backend, architecture)

            from ..llm.providers import LLMMessage
            messages = [
                LLMMessage(
                    role="system",
                    content="You are a senior software architect. Provide specific, actionable recommendations based on the code analysis. Focus on high-impact improvements. Respond in JSON format."
                ),
                LLMMessage(role="user", content=prompt)
            ]

            response = await router.generate(messages, max_tokens=1500, temperature=0.3)

            # Parse LLM response
            import json
            import re

            content = response.content
            json_match = re.search(r'\[[\s\S]*\]', content)
            if json_match:
                llm_recs = json.loads(json_match.group())
                return [
                    Recommendation(
                        priority=r.get("priority", "medium"),
                        category=r.get("category", "general"),
                        title=r.get("title", ""),
                        description=r.get("description", ""),
                        impact=r.get("impact") or "Improves code quality and maintainability",
                        effort=r.get("effort") or "medium",
                    )
                    for r in llm_recs[:5]
                ]

        except Exception as e:
            logger.warning(f"LLM recommendations failed: {e}")

        return []

    def _build_llm_prompt(
        self,
        context: CodebaseContext,
        frontend: Optional[FrontendAnalysis],
        backend: Optional[BackendAnalysis],
        architecture: Optional[ArchitectureAnalysis]
    ) -> str:
        """Build prompt for LLM recommendations"""
        parts = [
            f"# Code Analysis for: {context.platform_purpose}",
            f"Platform type: {context.platform_type.value}",
            f"Tech stack: {', '.join(context.tech_stack.frameworks[:5])}",
            "",
        ]

        if frontend:
            parts.extend([
                "## Frontend Analysis",
                f"Score: {frontend.score}/10",
                f"Components: {frontend.component_count}",
                f"Issues: {len(frontend.issues)}",
                "",
            ])

        if backend:
            parts.extend([
                "## Backend Analysis",
                f"Score: {backend.score}/10",
                f"Endpoints: {len(backend.endpoints)}",
                f"Security findings: {len(backend.security_findings)}",
                "",
            ])

        if architecture:
            parts.extend([
                "## Architecture",
                f"Score: {architecture.score}/10",
                f"Complexity: {architecture.total_complexity}",
                f"Circular deps: {len(architecture.circular_dependencies)}",
                "",
            ])

        parts.extend([
            "Based on this analysis, provide 3-5 specific recommendations as JSON array:",
            '[{"priority": "high|medium|low", "category": "security|performance|ux|architecture", "title": "...", "description": "...", "impact": "...", "effort": "low|medium|high"}]'
        ])

        return '\n'.join(parts)

    def _get_auth_example(self, frameworks: List[str]) -> Optional[str]:
        """Get auth implementation example"""
        if "FastAPI" in frameworks:
            return '''from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials = Depends(security)):
    token = credentials.credentials
    # Verify JWT token
    return verify_token(token)

@app.get("/protected")
async def protected_route(user = Depends(get_current_user)):
    return {"user": user}'''

        if "Express.js" in frameworks or "NestJS" in frameworks:
            return '''import jwt from 'jsonwebtoken';

const authMiddleware = (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });

  try {
    req.user = jwt.verify(token, process.env.JWT_SECRET);
    next();
  } catch {
    return res.status(401).json({ error: 'Invalid token' });
  }
};'''

        return None

    def _get_validation_example(self, frameworks: List[str]) -> Optional[str]:
        """Get validation implementation example"""
        if "FastAPI" in frameworks:
            return '''from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

@app.post("/users")
async def create_user(user: UserCreate):  # Auto-validated
    return {"email": user.email}'''

        if any(f in frameworks for f in ["Express.js", "NestJS", "Next.js"]):
            return '''import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

// In route handler
const result = UserSchema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json({ errors: result.error.issues });
}'''

        return None

    def _get_loading_example(self, frameworks: List[str]) -> Optional[str]:
        """Get loading state example"""
        if any(f in frameworks for f in ["React", "Next.js"]):
            return '''import { Suspense } from 'react';
import { Skeleton } from '@/components/ui/skeleton';

function LoadingState() {
  return <Skeleton className="w-full h-[200px]" />;
}

// Usage
<Suspense fallback={<LoadingState />}>
  <AsyncComponent />
</Suspense>'''

        return None

    def _deduplicate(self, recs: List[Recommendation]) -> List[Recommendation]:
        """Remove duplicate recommendations"""
        seen = set()
        unique = []

        for rec in recs:
            key = (rec.title.lower()[:50], rec.category)
            if key not in seen:
                seen.add(key)
                unique.append(rec)

        return unique

    def _prioritize(self, recs: List[Recommendation]) -> List[Recommendation]:
        """Sort recommendations by priority and impact"""
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        return sorted(recs, key=lambda r: priority_order.get(r.priority, 2))


# Convenience function
async def generate_recommendations(
    context: CodebaseContext,
    frontend: Optional[FrontendAnalysis] = None,
    backend: Optional[BackendAnalysis] = None,
    architecture: Optional[ArchitectureAnalysis] = None
) -> List[Recommendation]:
    """Generate recommendations from analysis results"""
    engine = RecommendationEngine()
    return await engine.generate_recommendations(context, frontend, backend, architecture)
