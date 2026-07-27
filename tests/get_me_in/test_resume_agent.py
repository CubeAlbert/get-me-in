"""Resume declarative AgentSpec contracts."""

import unittest

from src.get_me_in.agents.resume import build_resume_spec
from src.get_me_in.domain.agents import Capability


class ResumeAgentSpecTests(unittest.TestCase):
    def test_resume_spec_preserves_capabilities_and_temperature(self) -> None:
        spec = build_resume_spec()

        self.assertEqual(0.2, spec.temperature)
        self.assertNotIn(Capability.ROUTE, spec.capabilities)
        self.assertTrue({
            Capability.SYSTEM, Capability.PLAN, Capability.INTERACTION,
            Capability.WEB_SEARCH, Capability.EXTERNAL_FILE_READ,
            Capability.RETURN_TO_MAIN, Capability.WORKSPACE_READ,
            Capability.WORKSPACE_WRITE, Capability.WORKSPACE_OPEN,
            Capability.RESUME_ARTIFACT, Capability.KNOWLEDGE_QUERY,
        } <= spec.capabilities)
