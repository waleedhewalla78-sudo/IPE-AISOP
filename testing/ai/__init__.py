"""IPE AI-Augmented Testing Framework.

Orchestrates 6 AI testing agents for the IPE platform:
1. Test Generation — produces test cases from requirements/API specs
2. Regression — prioritizes and executes regression suites
3. Self-Healing — repairs broken selectors/selectors
4. Visual — detects UI regressions via screenshot diff
5. Exploratory — suggests risk-based charters
6. Optimization — reduces suite size while maintaining coverage

Human judgment is REQUIRED for: business logic validation, release decisions,
compliance verification, critical workflow approval.
"""

from testing.ai.agents.generator import TestGenerationAgent
from testing.ai.agents.regression import RegressionAgent
from testing.ai.agents.self_healing import SelfHealingAgent
from testing.ai.agents.visual import VisualTestingAgent
from testing.ai.agents.exploratory import ExploratoryTestingAgent
from testing.ai.agents.optimizer import TestOptimizationAgent

__all__ = [
    "TestGenerationAgent",
    "RegressionAgent",
    "SelfHealingAgent",
    "VisualTestingAgent",
    "ExploratoryTestingAgent",
    "TestOptimizationAgent",
]