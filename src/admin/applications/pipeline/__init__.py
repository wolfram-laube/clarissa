"""Pipeline module - Automated job application workflow"""

from .crawler import FreelancermapScraper, ProjectCrawler
from .matcher import ProjectMatcher
from .profiles import PROFILES

# Alias for convenience
FreelancerMapCrawler = FreelancermapScraper

__all__ = ["PROFILES", "FreelancermapScraper", "FreelancerMapCrawler", "ProjectCrawler", "ProjectMatcher"]
