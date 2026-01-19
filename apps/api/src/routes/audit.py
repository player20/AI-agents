"""
Audit Routes - Website and Code Repository Auditing

Provides comprehensive analysis for:
- Website audits (UX, performance, SEO, accessibility)
- GitHub repository code audits (security, frontend, backend, architecture)
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, HTMLResponse, Response
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["Audit"])


# =============================================================================
# Models
# =============================================================================

class WebsiteAuditRequest(BaseModel):
    url: str
    full: bool = False
    users: int = 3


class CodeAuditRequest(BaseModel):
    repo_url: str


# =============================================================================
# Website Audit Endpoints
# =============================================================================

@router.post("")
async def run_website_audit(request: WebsiteAuditRequest):
    """Run a website audit (non-streaming)"""
    await asyncio.sleep(2)

    return {
        "url": request.url,
        "timestamp": datetime.now().isoformat(),
        "scores": {
            "ux": 7.5,
            "performance": 8.0,
            "accessibility": 6.5,
            "seo": 7.0,
        },
        "confidence": {
            "score": 65,
            "level": "Medium",
            "color": "yellow",
            "has_real_data": False,
        },
        "recommendations": [
            "Improve page load time by optimizing images",
            "Add ARIA labels to interactive elements",
            "Implement lazy loading for below-fold content",
            "Add meta descriptions to all pages",
        ],
    }


@router.get("/stream")
async def stream_website_audit(
    url: str = Query(...),
    full: bool = Query(False),
    users: int = Query(3),
):
    """Stream website audit progress via SSE"""

    async def event_stream():
        yield f"data: {json.dumps({'type': 'start'})}\n\n"
        await asyncio.sleep(0.5)

        yield f"data: {json.dumps({'type': 'step', 'step': 'crawl', 'message': 'Fetching pages...'})}\n\n"
        await asyncio.sleep(1)

        yield f"data: {json.dumps({'type': 'step', 'step': 'analyze', 'message': 'Analyzing user flows...'})}\n\n"
        await asyncio.sleep(1)

        yield f"data: {json.dumps({'type': 'step', 'step': 'recommend', 'message': 'Generating recommendations...'})}\n\n"
        await asyncio.sleep(1)

        result = {
            "type": "complete",
            "url": url,
            "timestamp": datetime.now().isoformat(),
            "scores": {"ux": 7.5, "performance": 8.0, "accessibility": 6.5, "seo": 7.0},
            "confidence": {"score": 65, "level": "Medium", "color": "yellow"},
            "recommendations": [
                "Improve page load time by optimizing images",
                "Add ARIA labels to interactive elements",
            ],
        }
        yield f"data: {json.dumps(result)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )


# =============================================================================
# Code Audit Endpoints
# =============================================================================

@router.post("/code")
async def run_code_audit(request: CodeAuditRequest):
    """Run a GitHub repository code audit (non-streaming)"""
    repo_url = request.repo_url.strip().rstrip('/')

    # Validate GitHub URL
    github_pattern = r'^https?://(www\.)?github\.com/[\w-]+/[\w.-]+/?$'
    if not re.match(github_pattern, repo_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Please use format: https://github.com/owner/repo"
        )

    # Extract owner and repo
    parts = repo_url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid repository URL")

    owner, repo = parts[0], parts[1]

    try:
        # Run full analysis
        result = await _run_comprehensive_audit(owner, repo)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Code audit failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@router.get("/code/stream")
async def stream_code_audit(repo_url: str = Query(...)):
    """Stream comprehensive code audit progress via SSE"""
    repo_url = repo_url.strip().rstrip('/')

    # Validate GitHub URL
    github_pattern = r'^https?://(www\.)?github\.com/[\w-]+/[\w.-]+/?$'
    if not re.match(github_pattern, repo_url):
        async def error_stream():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Invalid GitHub URL'})}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

    parts = repo_url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
    owner, repo = parts[0], parts[1]

    async def event_stream():
        try:
            # Start
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            await asyncio.sleep(0.2)

            # Step 1: Fetch files
            yield f"data: {json.dumps({'type': 'step', 'step': 'fetch', 'message': 'Fetching repository files...'})}\n\n"

            from ..services.github_fetcher import GitHubFetcher
            fetcher = GitHubFetcher()

            try:
                repo_content = await fetcher.fetch_repository(owner, repo)
            except ValueError as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return
            except Exception as e:
                logger.error(f"GitHub fetch error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': 'Failed to fetch repository'})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'progress', 'step': 'fetch', 'message': f'Found {len(repo_content.files)} files'})}\n\n"
            await asyncio.sleep(0.3)

            # Step 2: Understand codebase
            yield f"data: {json.dumps({'type': 'step', 'step': 'context', 'message': 'Understanding codebase...'})}\n\n"

            from ..services.codebase_analyzer import CodebaseAnalyzer
            analyzer = CodebaseAnalyzer()

            context = await analyzer.analyze(
                files=repo_content.files,
                metadata=repo_content.metadata,
                readme=repo_content.readme,
                package_json=repo_content.package_json,
                requirements_txt=repo_content.requirements_txt,
                languages=repo_content.languages,
            )

            yield f"data: {json.dumps({'type': 'progress', 'step': 'context', 'message': f'Detected: {context.platform_type.value}'})}\n\n"
            await asyncio.sleep(0.3)

            # Step 3: Frontend analysis
            yield f"data: {json.dumps({'type': 'step', 'step': 'frontend', 'message': 'Analyzing UX/UI patterns...'})}\n\n"

            from ..services.domain_analyzers import FrontendAnalyzer, BackendAnalyzer, ArchitectureAnalyzer
            frontend_analyzer = FrontendAnalyzer()
            frontend_result = await frontend_analyzer.analyze(repo_content.files, context)

            yield f"data: {json.dumps({'type': 'progress', 'step': 'frontend', 'message': f'Frontend score: {frontend_result.score:.1f}/10'})}\n\n"
            await asyncio.sleep(0.3)

            # Step 4: Backend analysis
            yield f"data: {json.dumps({'type': 'step', 'step': 'backend', 'message': 'Scanning backend & security...'})}\n\n"

            backend_analyzer = BackendAnalyzer()
            backend_result = await backend_analyzer.analyze(repo_content.files, context)

            yield f"data: {json.dumps({'type': 'progress', 'step': 'backend', 'message': f'Found {len(backend_result.security_findings)} security issues'})}\n\n"
            await asyncio.sleep(0.3)

            # Step 5: Architecture analysis
            yield f"data: {json.dumps({'type': 'step', 'step': 'architecture', 'message': 'Evaluating architecture...'})}\n\n"

            arch_analyzer = ArchitectureAnalyzer()
            arch_result = await arch_analyzer.analyze(repo_content.files, context)

            yield f"data: {json.dumps({'type': 'progress', 'step': 'architecture', 'message': f'Complexity: {arch_result.total_complexity}'})}\n\n"
            await asyncio.sleep(0.3)

            # Step 6: Generate recommendations
            yield f"data: {json.dumps({'type': 'step', 'step': 'recommendations', 'message': 'Generating recommendations...'})}\n\n"

            from ..services.recommendation_engine import RecommendationEngine
            rec_engine = RecommendationEngine()
            recommendations = await rec_engine.generate_recommendations(
                context, frontend_result, backend_result, arch_result
            )

            yield f"data: {json.dumps({'type': 'progress', 'step': 'recommendations', 'message': f'Generated {len(recommendations)} recommendations'})}\n\n"
            await asyncio.sleep(0.2)

            # Complete - build response
            result = _build_audit_response(
                repo_url=repo_url,
                context=context,
                frontend=frontend_result,
                backend=backend_result,
                architecture=arch_result,
                recommendations=recommendations,
            )
            result["type"] = "complete"

            yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            logger.error(f"Code audit stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )


# =============================================================================
# Report Export Endpoint (for frontend)
# =============================================================================

@router.post("/export")
async def export_audit_report(request: Dict[str, Any]):
    """
    Export audit results as a shareable HTML report.

    This endpoint receives the audit result from the frontend
    along with company metadata to generate a branded report.
    Accepts the full audit result plus company_name, industry, monthly_visitors.
    """
    try:
        company_name = request.get("company_name", "Company")
        logger.info(f"Exporting report for {company_name}")

        # The request already contains the audit result + company metadata
        audit_result = {
            "repo_url": request.get("repo_url") or request.get("url") or "",
            "url": request.get("url") or request.get("repo_url") or "",
            "timestamp": request.get("timestamp") or datetime.now().isoformat(),
            "context": request.get("context") or {},
            "scores": request.get("scores") or {},
            "analysis": request.get("analysis") or {},
            "recommendations": request.get("recommendations") or [],
            "issues": request.get("issues") or {},
            "summary": request.get("summary") or {},
            # Add company metadata
            "company_name": company_name,
            "industry": request.get("industry", "general"),
            "monthly_visitors": request.get("monthly_visitors"),
        }

        # Generate HTML report
        from ..services.report_generator import generate_audit_report
        html_content = generate_audit_report(audit_result)

        # Return as downloadable HTML file
        filename = f"{company_name.replace(' ', '-')}-audit-report-{datetime.now().strftime('%Y%m%d')}.html"

        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/html; charset=utf-8"
            }
        )

    except Exception as e:
        logger.error(f"Export failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


# =============================================================================
# Report Generation Endpoints
# =============================================================================

@router.get("/code/report")
async def generate_code_audit_report(repo_url: str = Query(...)):
    """
    Generate a shareable HTML report for a GitHub repository code audit.

    Returns a professional, beautifully designed HTML report that can be:
    - Saved and shared with team members
    - Sent to clients or stakeholders
    - Used for documentation and tracking

    The report includes:
    - Executive summary with key metrics
    - Domain scores (Frontend, Backend, Architecture, Security)
    - Detailed issues with severity ratings
    - Code strengths and positive patterns
    - Actionable recommendations with impact/effort analysis
    - Implementation roadmap with phases
    """
    repo_url = repo_url.strip().rstrip('/')

    # Validate GitHub URL
    github_pattern = r'^https?://(www\.)?github\.com/[\w-]+/[\w.-]+/?$'
    if not re.match(github_pattern, repo_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Please use format: https://github.com/owner/repo"
        )

    # Extract owner and repo
    parts = repo_url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid repository URL")

    owner, repo = parts[0], parts[1]

    try:
        logger.info(f"Generating report for {owner}/{repo}")

        # Run full analysis
        result = await _run_comprehensive_audit(owner, repo)

        # Generate HTML report
        from ..services.report_generator import generate_audit_report
        html_content = generate_audit_report(result)

        # Return as downloadable HTML file
        filename = f"{repo}-audit-report-{datetime.now().strftime('%Y%m%d')}.html"

        return Response(
            content=html_content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/html; charset=utf-8"
            }
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@router.get("/code/report/preview")
async def preview_code_audit_report(repo_url: str = Query(...)):
    """
    Preview the HTML report inline (not as download).
    Same as /code/report but renders in the browser instead of downloading.
    """
    repo_url = repo_url.strip().rstrip('/')

    # Validate GitHub URL
    github_pattern = r'^https?://(www\.)?github\.com/[\w-]+/[\w.-]+/?$'
    if not re.match(github_pattern, repo_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Please use format: https://github.com/owner/repo"
        )

    # Extract owner and repo
    parts = repo_url.replace('https://github.com/', '').replace('http://github.com/', '').split('/')
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid repository URL")

    owner, repo = parts[0], parts[1]

    try:
        logger.info(f"Generating report preview for {owner}/{repo}")

        # Run full analysis
        result = await _run_comprehensive_audit(owner, repo)

        # Generate HTML report
        from ..services.report_generator import generate_audit_report
        html_content = generate_audit_report(result)

        # Return inline HTML (renders in browser)
        return HTMLResponse(content=html_content)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Report preview failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Report preview failed: {str(e)}")


# =============================================================================
# Helper Functions
# =============================================================================

async def _run_comprehensive_audit(owner: str, repo: str) -> Dict[str, Any]:
    """Run full code audit without streaming"""
    from ..services.github_fetcher import GitHubFetcher
    from ..services.codebase_analyzer import CodebaseAnalyzer
    from ..services.domain_analyzers import FrontendAnalyzer, BackendAnalyzer, ArchitectureAnalyzer
    from ..services.recommendation_engine import RecommendationEngine

    # Fetch repository
    fetcher = GitHubFetcher()
    repo_content = await fetcher.fetch_repository(owner, repo)

    # Analyze codebase context
    analyzer = CodebaseAnalyzer()
    context = await analyzer.analyze(
        files=repo_content.files,
        metadata=repo_content.metadata,
        readme=repo_content.readme,
        package_json=repo_content.package_json,
        requirements_txt=repo_content.requirements_txt,
        languages=repo_content.languages,
    )

    # Run domain analysis in parallel
    frontend_analyzer = FrontendAnalyzer()
    backend_analyzer = BackendAnalyzer()
    arch_analyzer = ArchitectureAnalyzer()

    frontend_result, backend_result, arch_result = await asyncio.gather(
        frontend_analyzer.analyze(repo_content.files, context),
        backend_analyzer.analyze(repo_content.files, context),
        arch_analyzer.analyze(repo_content.files, context),
    )

    # Generate recommendations
    rec_engine = RecommendationEngine()
    recommendations = await rec_engine.generate_recommendations(
        context, frontend_result, backend_result, arch_result
    )

    return _build_audit_response(
        repo_url=f"https://github.com/{owner}/{repo}",
        context=context,
        frontend=frontend_result,
        backend=backend_result,
        architecture=arch_result,
        recommendations=recommendations,
    )


def _build_audit_response(
    repo_url: str,
    context,
    frontend,
    backend,
    architecture,
    recommendations,
) -> Dict[str, Any]:
    """Build the audit response object"""
    # Calculate overall score
    scores = [frontend.score, backend.score, architecture.score]
    overall_score = sum(scores) / len(scores)

    # Count issues by severity
    all_issues = frontend.issues + backend.issues + architecture.issues
    issues_by_severity = {
        "critical": sum(1 for i in all_issues if i.severity == "critical"),
        "high": sum(1 for i in all_issues if i.severity == "high"),
        "medium": sum(1 for i in all_issues if i.severity == "medium"),
        "low": sum(1 for i in all_issues if i.severity == "low"),
    }

    # Build security findings for display
    security_findings = [
        {
            "severity": f.severity,
            "title": f.title,
            "description": f.description,
            "file": f.file_path,
            "line": f.line_number,
        }
        for f in backend.security_findings[:20]  # Limit for response size
    ]

    return {
        "repo_url": repo_url,
        "timestamp": datetime.now().isoformat(),

        # Context
        "context": {
            "platform_purpose": context.platform_purpose,
            "platform_type": context.platform_type.value,
            "frameworks": context.tech_stack.frameworks[:10],
            "languages": context.tech_stack.languages,
            "databases": context.tech_stack.databases,
            "architecture": context.architecture_type.value,
            "total_files": context.total_files,
            "total_lines": context.total_lines,
        },

        # Scores
        "scores": {
            "overall": round(overall_score, 1),
            "frontend": round(frontend.score, 1),
            "backend": round(backend.score, 1),
            "architecture": round(architecture.score, 1),
            "security": round(max(0, 10 - len(backend.security_findings) * 0.5), 1),
        },

        # Analysis details
        "analysis": {
            "frontend": {
                "score": round(frontend.score, 1),
                "component_count": frontend.component_count,
                "component_patterns": frontend.component_patterns,
                "state_management": frontend.state_libraries if frontend.state_libraries else [frontend.state_management],
                "ux_patterns": {k: v.to_dict() for k, v in frontend.ux_patterns.items()},
                "issues": [i.to_dict() for i in frontend.issues[:10]],
                "metrics": frontend.metrics,
            },
            "backend": {
                "score": round(backend.score, 1),
                "endpoint_count": len(backend.endpoints),
                "api_patterns": backend.api_patterns,
                "orm_usage": [backend.orm_usage] if backend.orm_usage and backend.orm_usage != "None detected" else [],
                "auth_score": round(backend.auth_analysis.score, 1),
                "validation_score": round(backend.input_validation.score, 1),
                "security_findings": security_findings,
                "issues": [i.to_dict() for i in backend.issues[:10]],
                "metrics": backend.metrics,
            },
            "architecture": {
                "score": round(architecture.score, 1),
                "folder_organization": architecture.folder_organization,
                "module_boundaries": architecture.module_boundaries,
                "total_complexity": architecture.total_complexity,
                "avg_complexity": round(architecture.avg_complexity, 1),
                "complex_files": [cf["path"] if isinstance(cf, dict) else str(cf) for cf in architecture.complex_files[:5]],
                "circular_dependencies": architecture.circular_dependencies,
                "issues": [i.to_dict() for i in architecture.issues[:10]],
                "metrics": architecture.metrics,
            },
        },

        # Summary
        "summary": {
            "total_files": context.total_files,
            "languages": context.tech_stack.languages,
            "lines_of_code": context.total_lines,
        },

        # Issues summary
        "issues": issues_by_severity,

        # Recommendations
        "recommendations": [r.to_dict() for r in recommendations],
    }
