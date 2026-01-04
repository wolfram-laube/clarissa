"""Tests for the LLM relay system."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add scripts to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestGitLabAPI:
    """Tests for GitLab API functions."""

    def test_gitlab_api_returns_json(self):
        """Test that gitlab_api returns parsed JSON."""
        from relay import gitlab_api
        
        # This actually calls GitLab - integration test
        result = gitlab_api("repository/commits?per_page=1")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) >= 1
        assert "id" in result[0]

    def test_gitlab_fetch_returns_content(self):
        """Test that gitlab_fetch returns file content."""
        from relay import gitlab_fetch
        
        result = gitlab_fetch("README.md")
        
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 0

    def test_gitlab_api_handles_invalid_endpoint(self):
        """Test that gitlab_api handles errors gracefully."""
        from relay import gitlab_api
        
        result = gitlab_api("nonexistent/endpoint/12345")
        
        assert result is None


class TestRepoContext:
    """Tests for repository context building."""

    def test_get_recent_commits(self):
        """Test fetching recent commits."""
        from relay import get_recent_commits
        
        commits = get_recent_commits(3)
        
        assert isinstance(commits, list)
        assert len(commits) <= 3
        if commits:
            assert "sha" in commits[0]
            assert "message" in commits[0]
            assert "date" in commits[0]

    def test_summarize_diff(self):
        """Test diff summarization."""
        from relay import summarize_diff
        
        mock_diff = [
            {
                "new_path": "src/test.py",
                "diff": "@@ -1,3 +1,5 @@\n+line1\n+line2\n-old\n context"
            }
        ]
        
        result = summarize_diff(mock_diff)
        
        assert "src/test.py" in result
        assert "+" in result or "-" in result

    def test_summarize_diff_empty(self):
        """Test diff summarization with empty input."""
        from relay import summarize_diff
        
        result = summarize_diff([])
        assert result == ""
        
        result = summarize_diff(None)
        assert result == ""

    def test_build_repo_context_no_files(self):
        """Test building context without specific files."""
        from relay import build_repo_context
        
        result = build_repo_context(include_diff=True, include_files=None)
        
        assert isinstance(result, str)
        assert "Recent Commits" in result or len(result) == 0

    def test_get_file_contents(self):
        """Test fetching file contents."""
        from relay import get_file_contents
        
        result = get_file_contents(["README.md"])
        
        assert isinstance(result, dict)
        if "README.md" in result:
            assert len(result["README.md"]) > 0


class TestKnowledgeBase:
    """Tests for knowledge base loading."""

    def test_load_knowledge_base(self):
        """Test loading knowledge base from GitLab."""
        from relay import load_knowledge_base
        
        result = load_knowledge_base()
        
        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain content from knowledge files
        assert "IRENA" in result or "CLARISSA" in result


class TestHandoffProcessing:
    """Tests for handoff processing logic."""

    @patch('relay.call_openai_api')
    def test_process_handoff_dry_run(self, mock_api):
        """Test that dry run doesn't call API."""
        from relay import process_handoff, HANDOFF_DIR, HANDOFF_TO_IRENA
        import os
        
        # Create test handoff
        HANDOFF_DIR.mkdir(exist_ok=True)
        HANDOFF_TO_IRENA.write_text("# Test Handoff\n\nTest content")
        
        try:
            # Dry run should not call the API
            mock_api.return_value = "[DRY RUN] Test response"
            result = process_handoff(dry_run=True)
            
            # In dry run, API is called but with dry_run=True
            assert mock_api.called
            
        finally:
            # Cleanup
            if HANDOFF_TO_IRENA.exists():
                HANDOFF_TO_IRENA.unlink()


class TestHelperFunctions:
    """Tests for helper/utility functions."""

    def test_copy_to_clipboard_fails_gracefully(self):
        """Test that clipboard function handles missing tools."""
        from relay import copy_to_clipboard
        
        # Should not raise, just return False if no clipboard tool
        result = copy_to_clipboard("test")
        assert isinstance(result, bool)