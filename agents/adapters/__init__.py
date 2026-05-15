"""ATS adapter registry — maps site family names to adapter classes."""

from __future__ import annotations

from agents.adapters.ats_ashby import AshbyAdapter
from agents.adapters.ats_generic import GenericAdapter
from agents.adapters.ats_glassdoor import GlassdoorAdapter
from agents.adapters.ats_greenhouse import GreenhouseAdapter
from agents.adapters.ats_indeed import IndeedAdapter
from agents.adapters.ats_lever import LeverAdapter
from agents.adapters.ats_linkedin import LinkedInAdapter
from agents.adapters.ats_wellfound import WellfoundAdapter
from agents.adapters.ats_workday import WorkdayAdapter
from agents.adapters.base import ATSAdapter

REGISTRY: dict[str, type[ATSAdapter]] = {
    "greenhouse": GreenhouseAdapter,
    "lever": LeverAdapter,
    "ashby": AshbyAdapter,
    "workday": WorkdayAdapter,
    "indeed": IndeedAdapter,
    "glassdoor": GlassdoorAdapter,
    "wellfound": WellfoundAdapter,
    "linkedin": LinkedInAdapter,
    "generic": GenericAdapter,
}

__all__ = [
    "ATSAdapter",
    "REGISTRY",
    "GreenhouseAdapter",
    "LeverAdapter",
    "AshbyAdapter",
    "WorkdayAdapter",
    "IndeedAdapter",
    "GlassdoorAdapter",
    "WellfoundAdapter",
    "LinkedInAdapter",
    "GenericAdapter",
]
