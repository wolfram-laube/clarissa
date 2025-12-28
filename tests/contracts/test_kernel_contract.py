from orsa_kernel.core import NativeKernel

def test_kernel_explain_contract_has_string():
    k = NativeKernel()
    msg = k.explain("WELL A RATE 90", {"converged": True, "errors": []})
    assert isinstance(msg, str)
    assert len(msg.strip()) > 0

def test_kernel_explain_mentions_state():
    k = NativeKernel()
    ok = k.explain("CASE", {"converged": True, "errors": []}).lower()
    bad = k.explain("CASE", {"converged": False, "errors": ["E"]}).lower()
    assert ("stabil" in ok) or ("converg" in ok) or ("ok" in ok)
    assert ("diverg" in bad) or ("fail" in bad) or ("error" in bad)
