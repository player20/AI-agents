"""
GitHub Repository Fetcher

Fetches actual code files from GitHub repositories for deep code analysis.
Supports both small repos (via Contents API) and large repos (via archive download).
"""

from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import asyncio
import base64
import fnmatch
import hashlib
import json
import logging
import os
import tempfile
import zipfile

import httpx

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file in the repository"""
    path: str
    size: int
    sha: str
    type: str  # "file" or "dir"
    download_url: Optional[str] = None


@dataclass
class RepositoryContent:
    """Complete repository content for analysis"""
    owner: str
    repo: str
    branch: str
    files: Dict[str, str]  # path -> content
    file_tree: List[FileInfo]
    metadata: Dict[str, Any]
    languages: Dict[str, int]  # language -> bytes
    readme: Optional[str] = None
    package_json: Optional[Dict] = None
    requirements_txt: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now().isoformat())


# File patterns to include in analysis
ANALYSIS_PATTERNS = {
    "frontend": [
        "*.tsx", "*.jsx", "*.vue", "*.svelte",
        "*.html", "*.css", "*.scss", "*.sass", "*.less",
        "*.astro", "*.mdx"
    ],
    "backend": [
        "*.py", "*.ts", "*.js", "*.go", "*.java",
        "*.rb", "*.php", "*.rs", "*.kt", "*.cs",
        "*.scala", "*.ex", "*.exs"
    ],
    "config": [
        "package.json", "tsconfig.json", "*.config.js", "*.config.ts",
        "requirements.txt", "pyproject.toml", "Cargo.toml",
        "go.mod", "pom.xml", "build.gradle",
        ".env.example", "docker-compose.yml", "Dockerfile"
    ],
    "docs": [
        "README.md", "README.rst", "CHANGELOG.md",
        "docs/**/*.md", "*.md"
    ],
}

# Patterns to skip
SKIP_PATTERNS = [
    # Dependencies
    "node_modules/**", "vendor/**", "venv/**", ".venv/**",
    "__pycache__/**", ".pytest_cache/**", ".mypy_cache/**",

    # Build outputs
    "dist/**", "build/**", ".next/**", ".nuxt/**",
    "out/**", "target/**", "bin/**", "obj/**",

    # Version control
    ".git/**", ".svn/**", ".hg/**",

    # IDE
    ".idea/**", ".vscode/**", "*.swp", "*.swo",

    # Generated/minified
    "*.min.js", "*.min.css", "*.map",
    "*.bundle.js", "*.chunk.js",

    # Lock files (large, not useful for analysis)
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "poetry.lock", "Cargo.lock", "composer.lock",

    # Assets
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.ico", "*.svg",
    "*.woff", "*.woff2", "*.ttf", "*.eot",
    "*.mp3", "*.mp4", "*.webm", "*.wav",
    "*.pdf", "*.zip", "*.tar", "*.gz",
]

# Maximum file size to fetch (1MB)
MAX_FILE_SIZE = 1 * 1024 * 1024

# Maximum total files to fetch
MAX_FILES = 500


class GitHubFetcher:
    """
    Fetch actual code files from GitHub repositories.

    Example:
        fetcher = GitHubFetcher()
        content = await fetcher.fetch_repository("vercel", "next.js")

        print(f"Found {len(content.files)} files")
        print(f"Platform: {content.readme[:200]}...")
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize fetcher with optional GitHub token.

        Args:
            token: GitHub personal access token for higher rate limits
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self._cache: Dict[str, RepositoryContent] = {}

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with optional auth"""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "CodeWeaver-Audit/1.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def fetch_repository(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None,
        use_cache: bool = True
    ) -> RepositoryContent:
        """
        Fetch repository structure and file contents.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (defaults to default branch)
            use_cache: Whether to use cached results

        Returns:
            RepositoryContent with files and metadata
        """
        cache_key = f"{owner}/{repo}/{branch or 'default'}"

        if use_cache and cache_key in self._cache:
            logger.info(f"Using cached content for {cache_key}")
            return self._cache[cache_key]

        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get repo metadata
            repo_data = await self._get_repo_metadata(client, owner, repo)

            if branch is None:
                branch = repo_data.get("default_branch", "main")

            # Get languages
            languages = await self._get_languages(client, owner, repo)

            # Get file tree
            file_tree = await self._get_file_tree(client, owner, repo, branch)

            # Filter files for analysis
            files_to_fetch = self._filter_files(file_tree)
            logger.info(f"Fetching {len(files_to_fetch)} files (filtered from {len(file_tree)})")

            # Fetch file contents
            files = await self._fetch_files(client, owner, repo, branch, files_to_fetch)

            # Extract special files
            readme = files.get("README.md") or files.get("readme.md")
            package_json = None
            if "package.json" in files:
                try:
                    package_json = json.loads(files["package.json"])
                except json.JSONDecodeError:
                    pass
            requirements_txt = files.get("requirements.txt")

            content = RepositoryContent(
                owner=owner,
                repo=repo,
                branch=branch,
                files=files,
                file_tree=file_tree,
                metadata=repo_data,
                languages=languages,
                readme=readme,
                package_json=package_json,
                requirements_txt=requirements_txt
            )

            # Cache the result
            self._cache[cache_key] = content

            return content

    async def _get_repo_metadata(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str
    ) -> Dict[str, Any]:
        """Get repository metadata"""
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            headers=self._get_headers()
        )

        if response.status_code == 404:
            raise ValueError(f"Repository {owner}/{repo} not found or is private")

        response.raise_for_status()
        return response.json()

    async def _get_languages(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str
    ) -> Dict[str, int]:
        """Get repository languages"""
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/languages",
            headers=self._get_headers()
        )

        if response.status_code == 200:
            return response.json()
        return {}

    async def _get_file_tree(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        branch: str
    ) -> List[FileInfo]:
        """Get recursive file tree using trees API"""
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}",
            params={"recursive": "1"},
            headers=self._get_headers()
        )

        if response.status_code != 200:
            logger.warning(f"Failed to get tree: {response.status_code}")
            return []

        data = response.json()
        files = []

        for item in data.get("tree", []):
            if item["type"] == "blob":  # Only files
                files.append(FileInfo(
                    path=item["path"],
                    size=item.get("size", 0),
                    sha=item["sha"],
                    type="file"
                ))

        return files

    def _filter_files(self, file_tree: List[FileInfo]) -> List[FileInfo]:
        """Filter files based on analysis patterns"""
        filtered = []

        for file_info in file_tree:
            path = file_info.path

            # Skip if matches skip patterns
            if self._matches_patterns(path, SKIP_PATTERNS):
                continue

            # Skip if too large
            if file_info.size > MAX_FILE_SIZE:
                logger.debug(f"Skipping large file: {path} ({file_info.size} bytes)")
                continue

            # Include if matches analysis patterns
            all_patterns = []
            for patterns in ANALYSIS_PATTERNS.values():
                all_patterns.extend(patterns)

            if self._matches_patterns(path, all_patterns):
                filtered.append(file_info)

        # Limit total files
        if len(filtered) > MAX_FILES:
            logger.warning(f"Limiting to {MAX_FILES} files (found {len(filtered)})")
            # Prioritize: config > docs > code
            config = [f for f in filtered if self._matches_patterns(f.path, ANALYSIS_PATTERNS["config"])]
            docs = [f for f in filtered if self._matches_patterns(f.path, ANALYSIS_PATTERNS["docs"])]
            code = [f for f in filtered if f not in config and f not in docs]

            filtered = config[:50] + docs[:50] + code[:MAX_FILES - 100]

        return filtered

    def _matches_patterns(self, path: str, patterns: List[str]) -> bool:
        """Check if path matches any pattern"""
        for pattern in patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
            # Handle ** patterns
            if "**" in pattern:
                parts = pattern.split("**")
                if len(parts) == 2:
                    prefix, suffix = parts
                    if path.startswith(prefix.rstrip("/")) and path.endswith(suffix.lstrip("/")):
                        return True
        return False

    async def _fetch_files(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        branch: str,
        files: List[FileInfo]
    ) -> Dict[str, str]:
        """Fetch file contents in parallel"""
        result = {}

        # Batch requests to avoid rate limiting
        batch_size = 20
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            tasks = [
                self._fetch_file_content(client, owner, repo, branch, f.path)
                for f in batch
            ]

            contents = await asyncio.gather(*tasks, return_exceptions=True)

            for file_info, content in zip(batch, contents):
                if isinstance(content, Exception):
                    logger.warning(f"Failed to fetch {file_info.path}: {content}")
                elif content is not None:
                    result[file_info.path] = content

            # Small delay between batches
            if i + batch_size < len(files):
                await asyncio.sleep(0.5)

        return result

    async def _fetch_file_content(
        self,
        client: httpx.AsyncClient,
        owner: str,
        repo: str,
        branch: str,
        path: str
    ) -> Optional[str]:
        """Fetch a single file's content"""
        # Try raw content first (faster, no rate limit)
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

        try:
            response = await client.get(raw_url)
            if response.status_code == 200:
                # Try to decode as text
                try:
                    return response.text
                except UnicodeDecodeError:
                    logger.debug(f"Binary file skipped: {path}")
                    return None
        except Exception as e:
            logger.debug(f"Raw fetch failed for {path}: {e}")

        # Fallback to Contents API
        try:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                params={"ref": branch},
                headers=self._get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("encoding") == "base64" and "content" in data:
                    try:
                        return base64.b64decode(data["content"]).decode("utf-8")
                    except (UnicodeDecodeError, ValueError):
                        return None
        except Exception as e:
            logger.debug(f"API fetch failed for {path}: {e}")

        return None

    async def download_archive(
        self,
        owner: str,
        repo: str,
        branch: Optional[str] = None
    ) -> Path:
        """
        Download and extract repository archive for large repos.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch name (defaults to default branch)

        Returns:
            Path to extracted directory
        """
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            # Get default branch if not specified
            if branch is None:
                repo_data = await self._get_repo_metadata(client, owner, repo)
                branch = repo_data.get("default_branch", "main")

            # Download zipball
            url = f"https://api.github.com/repos/{owner}/{repo}/zipball/{branch}"
            response = await client.get(url, headers=self._get_headers())
            response.raise_for_status()

            # Save to temp file
            temp_dir = Path(tempfile.mkdtemp())
            zip_path = temp_dir / "repo.zip"

            with open(zip_path, "wb") as f:
                f.write(response.content)

            # Extract
            extract_dir = temp_dir / "extracted"
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_dir)

            # Find the extracted folder (GitHub adds prefix)
            extracted_folders = list(extract_dir.iterdir())
            if extracted_folders:
                return extracted_folders[0]

            return extract_dir

    def categorize_file(self, path: str) -> str:
        """Categorize a file by its purpose"""
        for category, patterns in ANALYSIS_PATTERNS.items():
            if self._matches_patterns(path, patterns):
                return category
        return "other"

    def get_category_files(
        self,
        content: RepositoryContent,
        category: str
    ) -> Dict[str, str]:
        """Get files for a specific category"""
        patterns = ANALYSIS_PATTERNS.get(category, [])
        return {
            path: code
            for path, code in content.files.items()
            if self._matches_patterns(path, patterns)
        }


# Convenience function
async def fetch_github_repo(
    repo_url: str,
    token: Optional[str] = None
) -> RepositoryContent:
    """
    Fetch a GitHub repository from URL.

    Args:
        repo_url: GitHub repository URL
        token: Optional GitHub token

    Returns:
        RepositoryContent with files and metadata
    """
    import re

    # Parse URL
    pattern = r"github\.com[/:]([^/]+)/([^/\s\.]+)"
    match = re.search(pattern, repo_url)

    if not match:
        raise ValueError(f"Invalid GitHub URL: {repo_url}")

    owner, repo = match.groups()
    repo = repo.rstrip(".git")

    fetcher = GitHubFetcher(token=token)
    return await fetcher.fetch_repository(owner, repo)
