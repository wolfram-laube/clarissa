"""Tests for the LLM relay system.

All GitLab API interactions are mocked — unit tests must never
depend on network access or live credentials (GOV-001).
"""

import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

# Add scripts to path for importing relay
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


def _make_urlopen_mock(response_body: str | bytes):
    """Create a context-manager-compatible mock for urlopen."""
    if isinstance(response_body, str):
        response_body = response_body.encode()
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_body
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestGitLabAPI:
    """Tests for gitlab_api() — HTTP→JSON layer."""

    def test_returns_parsed_json_list(self):
        """gitlab_api returns parsed list from JSON response."""
        import relay

        payload = [{"id": "abc123", "title": "test commit"}]
        mock = _make_urlopen_mock(json.dumps(payload))

        with patch("urllib.request.urlopen", return_value=mock):
            result = relay.gitlab_api("repository/commits?per_page=1")

        assert result == payload

    def test_returns_parsed_json_dict(self):
        """gitlab_api returns parsed dict from JSON response."""
        import relay

        payload = {"name": "main", "protected": True}
        mock = _make_urlopen_mock(json.dumps(payload))

        with patch("urllib.request.urlopen", return_value=mock):
            result = relay.gitlab_api("repository/branches/main")

        assert result == payload

    def test_returns_none_on_401(self):
        """Missing or invalid token → None, no crash."""
        import relay

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = HTTPError(
                url="https://gitlab.com/api/v4/...",
                code=401, msg="Unauthorized", hdrs={}, fp=None,
            )
            result = relay.gitlab_api("repository/commits")

        assert result is None

    def test_returns_none_on_404(self):
        """Non-existent endpoint → None, no crash."""
        import relay

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = HTTPError(
                url="https://gitlab.com/api/v4/...",
                code=404, msg="Not Found", hdrs={}, fp=None,
            )
            result = relay.gitlab_api("nonexistent/endpoint")

        assert result is None

    def test_returns_none_on_network_error(self):
        """Network timeout / DNS failure → None, no crash."""
        import relay

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = URLError("Connection refused")
            result = relay.gitlab_api("repository/commits")

        assert result is None


class TestGitLabFetch:
    """Tests for gitlab_fetch() — raw file retrieval."""

    def test_returns_file_content(self):
        """gitlab_fetch returns decoded string content."""
        import relay

        content = "# CLARISSA\nReservoir simulation assistant"
        mock = _make_urlopen_mock(content)

        with patch("urllib.request.urlopen", return_value=mock):
            result = relay.gitlab_fetch("README.md")

        assert result == content
        assert "CLARISSA" in result

    def test_returns_none_on_missing_file(self):
        """Missing file → None."""
        import relay

        with patch("urllib.request.urlopen") as mock_open:
            mock_open.side_effect = HTTPError(
                url="https://gitlab.com/...",
                code=404, msg="Not Found", hdrs={}, fp=None,
            )
            result = relay.gitlab_fetch("nonexistent.py")

        assert result is None


class TestRepoContext:
    """Tests for commit/diff processing (pure logic + mocked API)."""

    def test_get_recent_commits(self):
        """get_recent_commits formats API response correctly."""
        import relay

        mock_commits = [
            {
                "id": "abc123def456",
                "short_id": "abc123d",
                "title": "feat: add sim engine",
                "created_at": "2026-02-22T09:00:00Z",
                "author_name": "Wolfram Laube",
            }
        ]

        with patch.object(relay, "gitlab_api", side_effect=[
            mock_commits,      # first call: list commits
            [{"new_path": "src/sim.py", "diff": "+new"}],  # second: diff
        ]):
            commits = relay.get_recent_commits(1)

        assert len(commits) == 1
        assert commits[0]["sha"] == "abc123d"
        assert commits[0]["message"] == "feat: add sim engine"
        assert commits[0]["date"] == "2026-02-22"

    def test_get_recent_commits_empty(self):
        """Empty repo → empty list."""
        import relay

        with patch.object(relay, "gitlab_api", return_value=[]):
            commits = relay.get_recent_commits(5)

        assert commits == []

    def test_get_recent_commits_api_failure(self):
        """API failure → empty list, no crash."""
        import relay

        with patch.object(relay, "gitlab_api", return_value=None):
            commits = relay.get_recent_commits(5)

        assert commits == []

    def test_summarize_diff(self):
        """Diff summary includes file paths and +/- counts."""
        import relay

        mock_diff = [
            {
                "new_path": "src/test.py",
                "diff": "@@ -1,3 +1,5 @@\n+line1\n+line2\n-old\n context",
            }
        ]

        result = relay.summarize_diff(mock_diff)
        assert "src/test.py" in result

    def test_summarize_diff_empty(self):
        """Empty or None diff → empty string."""
        import relay

        assert relay.summarize_diff([]) == ""
        assert relay.summarize_diff(None) == ""

    def test_summarize_diff_multiple_files(self):
        """Multiple files are all included in summary."""
        import relay

        mock_diff = [
            {"new_path": "src/a.py", "diff": "+added"},
            {"new_path": "src/b.py", "diff": "-removed"},
        ]

        result = relay.summarize_diff(mock_diff)
        assert "src/a.py" in result
        assert "src/b.py" in result

    def test_get_file_contents(self):
        """get_file_contents returns dict of path→content."""
        import relay

        with patch.object(relay, "gitlab_fetch", return_value="# README"):
            result = relay.get_file_contents(["README.md"])

        assert isinstance(result, dict)
        assert result["README.md"] == "# README"

    def test_get_file_contents_skips_missing(self):
        """Missing files are excluded from result."""
        import relay

        with patch.object(relay, "gitlab_fetch", return_value=None):
            result = relay.get_file_contents(["missing.py"])

        assert "missing.py" not in result


class TestKnowledgeBase:
    """Tests for knowledge base loading."""

    def test_load_knowledge_base_from_api(self):
        """Knowledge base loads via gitlab_fetch when local files absent."""
        import relay

        with patch.object(relay, "gitlab_fetch", return_value="CLARISSA knowledge"):
            with patch.object(Path, "exists", return_value=False):
                result = relay.load_knowledge_base()

        assert isinstance(result, str)
        assert len(result) > 0

    def test_load_knowledge_base_handles_missing_files(self):
        """All files missing → empty string, no crash."""
        import relay

        with patch.object(relay, "gitlab_fetch", return_value=None):
            with patch.object(Path, "exists", return_value=False):
                result = relay.load_knowledge_base()

        assert isinstance(result, str)
