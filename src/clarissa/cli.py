"""CLARISSA CLI.

Run:
  python -m clarissa --help
  python -m clarissa demo
"""

from __future__ import annotations
import argparse
from .agent.core import CLARISSAAgent
from .governance.policy import GovernancePolicy
from .simulators.mock import MockSimulator
from .kernel_bridge import KernelBridge


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="clarissa", description="CLARISSA prototype CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="Run a minimal governed simulator-in-the-loop demo")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.cmd == "demo":
        gov = GovernancePolicy()
        sim = MockSimulator()
        kernel = KernelBridge()  # bridge to clarissa_kernel (lab)
        agent = CLARISSAAgent(governance=gov, simulator=sim, kernel=kernel)
        agent.demo()
        return 0

    return 2
