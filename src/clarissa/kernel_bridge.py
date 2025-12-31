"""Bridge to the CLARISSA native kernel package (clarissa_kernel)."""

from __future__ import annotations
from . import __version__
from clarissa_kernel.core import NativeKernel


class KernelBridge(NativeKernel):
    # For now, KernelBridge simply uses the native kernel implementation.
    # This indirection makes it easy to evolve integration patterns later.
    pass
