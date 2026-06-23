from __future__ import annotations

import logging
import os

from ipe_shared.solver.interface import ISolver

logger = logging.getLogger(__name__)

_SOLVER_REGISTRY: dict[str, type[ISolver]] = {}


def register_solver(name: str, solver_cls: type[ISolver]) -> None:
    _SOLVER_REGISTRY[name.lower()] = solver_cls


def unregister_solver(name: str) -> None:
    _SOLVER_REGISTRY.pop(name.lower(), None)


class SolverFactory:
    _instance: SolverFactory | None = None

    def __init__(self):
        self._solvers: dict[str, ISolver] = {}
        self._default_name: str = os.environ.get("IPE_SOLVER_DEFAULT", "ortools")

    @classmethod
    def get_instance(cls) -> SolverFactory:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def register(cls, name: str, solver_class: type[ISolver]) -> None:
        register_solver(name, solver_class)

    @classmethod
    def create(cls, name: str, **kwargs) -> ISolver:
        instance = cls.get_instance()
        return instance.create_solver(name)

    def create_solver(
        self,
        name: str | None = None,
        fallback: str | None = "ortools",
    ) -> ISolver:
        solver_name = (name or self._default_name).lower()

        if solver_name in self._solvers:
            return self._solvers[solver_name]

        if not _SOLVER_REGISTRY:
            self._try_auto_register()

        solver_cls = _SOLVER_REGISTRY.get(solver_name)
        if solver_cls is None:
            raise ValueError(
                f"Unknown solver: {solver_name}."
                f" Available: {list(_SOLVER_REGISTRY.keys())}"
            )

        if solver_name == "gurobi" and fallback:
            fallback_cls = _SOLVER_REGISTRY.get(fallback)
            if fallback_cls:
                fallback_solver = fallback_cls()
                solver = solver_cls(fallback_solver=fallback_solver)
            else:
                solver = solver_cls()
        else:
            solver = solver_cls()

        self._solvers[solver_name] = solver
        return solver

    def _try_auto_register(self) -> None:
        try:
            from app.core.ortools_solver import ORToolsSolver
            register_solver("ortools", ORToolsSolver)
        except ImportError:
            logger.debug("ORTools solver not available for auto-registration")
        try:
            from app.core.gurobi_solver import GurobiSolver
            register_solver("gurobi", GurobiSolver)
        except ImportError:
            logger.debug("Gurobi solver not available for auto-registration")

    def get_solver(self, name: str | None = None) -> ISolver:
        return self.create_solver(name)

    @staticmethod
    def available_solvers() -> list[str]:
        return list(_SOLVER_REGISTRY.keys())
