"""Solver factory for cap-svc.

Registers ORToolsSolver and (optionally) GurobiSolver with the shared
SolverFactory so that the solver can be selected at runtime via
IPE_SOLVER_DEFAULT environment variable.
"""
from __future__ import annotations

import logging

from ipe_shared.solver.factory import register_solver

logger = logging.getLogger(__name__)


def register_cap_svc_solvers() -> None:
    from app.core.ortools_solver import ORToolsSolver

    register_solver("ortools", ORToolsSolver)

    try:
        from app.core.gurobi_solver import GurobiSolver

        register_solver("gurobi", GurobiSolver)
        logger.info("Registered GurobiSolver (license will be checked at solve time)")
    except ImportError:
        logger.debug("GurobiSolver not available (gurobipy not installed)")


register_cap_svc_solvers()