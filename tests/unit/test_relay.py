"""Tests for the LLM relay system."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add scripts to path for importing relay
SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))


class TestGitLabAPI:
    """Tests for GitLab API functions."""

    def test_gitlab_api_returns_json(self):
        """Test that gitlab_api returns parsed JSON."""
        import relay
        
        result = relay.gitlab_api("repository/commits?per_page=1")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "id" in result[0]

    def test_gitlab_fetch_returns_content(self):
        """Test that gitlab_fetch returns file content."""
        import relay
        
        result = relay.gitlab_fetch("README.md")
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_gitlab_api_handles_invalid_endpoint(self):
        """Test that gitlab_api handles errors gracefully."""
        import relay
        
        result = relay.gitlab_api("nonexistent/endpoint/12345")
        
        assert result is None


class TestRepoContext:
    """Tests for repository context building."""

    def test_get_recent_commits(self):
        """Test fetching recent commits."""
        import relay
        
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

    def test_get_file_contents(self):
        """Test fetching file contents."""
        import relay
        
        result = relay.get_file_contents(["README.md"])
        
        assert isinstance(result, dict)
        if "README.md" in result:
            assert len(result["README.md"]) > 0


class TestKnowledgeBase:
    """Tests for knowledge base loading."""

    def test_load_knowledge_base(self):
        """Test loading knowledge base from GitLab."""
        import relay
        
        result = relay.load_knowledge_base()
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain content from knowledge files
        assert "IRENA" in result or "CLARISSA" in result


class TestHelperFunctions:
    """Tests for helper/utility functions."""

    def test_copy_to_clipboard_fails_gracefully(self):
        """Test that clipboard function handles missing tools."""
        import relay
        
        # Should not raise, just return False if no clipboard tool
        result = relay.copy_to_clipboard("test")
        assert isinstance(result, bool)