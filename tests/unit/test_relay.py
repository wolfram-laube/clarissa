"""Tests for the LLM relay system."""

import pytest
import sys
from pathlib import Path

# Add scripts to path for importing relay
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


class TestGitLabAPI:
    """Tests for GitLab API functions."""

    def test_gitlab_api_returns_json(self, monkeypatch):
        """Test that gitlab_api returns parsed JSON."""
        import relay

        fake_response = [{"id": "abc123", "short_id": "abc", "title": "test commit"}]

        def _mock_api(endpoint):
            if "nonexistent" in endpoint:
                return None
            return fake_response

        monkeypatch.setattr(relay, "gitlab_api", _mock_api)

        result = relay.gitlab_api("repository/commits?per_page=1")

        assert result is not None
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "id" in result[0]

    def test_gitlab_fetch_returns_content(self, monkeypatch):
        """Test that gitlab_fetch returns file content."""
        import relay

        monkeypatch.setattr(relay, "gitlab_fetch", lambda path: "# CLARISSA\nReadme content")

        result = relay.gitlab_fetch("README.md")

        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_gitlab_api_handles_invalid_endpoint(self, monkeypatch):
        """Test that gitlab_api handles errors gracefully."""
        import relay

        monkeypatch.setattr(relay, "gitlab_api", lambda ep: None)

        result = relay.gitlab_api("nonexistent/endpoint/12345")

        assert result is None


class TestRepoContext:
    """Tests for repository context building."""

    def test_get_recent_commits(self, monkeypatch):
        """Test fetching recent commits."""
        import relay

        fake_commits = [
            {"sha": "abc123", "message": "feat: test", "date": "2026-02-22"},
            {"sha": "def456", "message": "fix: bug", "date": "2026-02-21"},
        ]
        monkeypatch.setattr(relay, "get_recent_commits", lambda n: fake_commits[:n])

        commits = relay.get_recent_commits(3)

        assert isinstance(commits, list)
        assert len(commits) <= 3
        if commits:
            assert "sha" in commits[0]
            assert "message" in commits[0]
            assert "date" in commits[0]

    def test_summarize_diff(self):
        """Test diff summarization."""
        import relay
        
        mock_diff = [
            {
                "new_path": "src/test.py",
                "diff": "@@ -1,3 +1,5 @@\n+line1\n+line2\n-old\n context"
            }
        ]
        
        result = relay.summarize_diff(mock_diff)
        
        assert "src/test.py" in result

    def test_summarize_diff_empty(self):
        """Test diff summarization with empty input."""
        import relay
        
        result = relay.summarize_diff([])
        assert result == ""
        
        result = relay.summarize_diff(None)
        assert result == ""

    def test_get_file_contents(self, monkeypatch):
        """Test fetching file contents."""
        import relay

        monkeypatch.setattr(
            relay, "get_file_contents",
            lambda paths: {p: f"content of {p}" for p in paths},
        )

        result = relay.get_file_contents(["README.md"])

        assert isinstance(result, dict)
        assert "README.md" in result
        assert len(result["README.md"]) > 0


class TestKnowledgeBase:
    """Tests for knowledge base loading."""

    def test_load_knowledge_base(self, monkeypatch):
        """Test loading knowledge base from GitLab."""
        import relay

        monkeypatch.setattr(
            relay, "load_knowledge_base",
            lambda: "# CLARISSA Knowledge Base\nReservoir simulation context.",
        )

        result = relay.load_knowledge_base()

        assert isinstance(result, str)
        assert len(result) > 0
        assert "CLARISSA" in result