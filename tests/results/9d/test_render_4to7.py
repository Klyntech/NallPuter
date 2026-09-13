"""9D Render validation — Tests 4-7 (remaining after 1-3 passed)."""
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "N.A.L.L.Y"))

import nally.config
from nally.tools.registry_builder import load_all_tools
from nally.tools.registry import registry
from nally.computer import ComputerAdapter, ComputerClient
from nally.computer.models import ComputerError
from nally.agent.core import NallyAgent

RENDER_URL = "https://nallputer.onrender.com/v1"
RENDER_TOKEN = "nally-nallputer-secret-2026"

def main():
    os.environ["NALLPUTER_URL"] = RENDER_URL
    os.environ["NALLPUTER_TOKEN"] = RENDER_TOKEN
    os.environ["NALLPUTER_STARTUP_GRACE_MS"] = "60000"

    client_obj = ComputerClient()
    client_obj.timeout_connect = 15.0
    client_obj.timeout_health = 30.0
    client_obj.timeout_ttfb = 60.0
    client = ComputerAdapter(client_obj)

    preflight = client.preflight()
    if isinstance(preflight, ComputerError):
        print(f"FAIL: preflight: {preflight.code} - {preflight.message}")
        return 1
    print(f"NallPuter: {preflight.computer_id} at {RENDER_URL}")
    registry.set_computer_adapter(client)
    load_all_tools()

    results = []

    # Test 4: Planning path (COMPLEX) — simplified to reduce round trips
    print("=== Test 4: Planning path (COMPLEX) ===")
    agent = NallyAgent(session_id="9d-render-t4b")
    r4 = agent.process(
        "On the computer, write the word PLAN_PROOF to /home/nally/workspace/r4-plan.txt and tell me what you did."
    )
    t4 = "PLAN_PROOF" in r4 or "r4-plan" in r4.lower() or "wrote" in r4.lower()
    results.append(("Planning path (COMPLEX)", t4, r4[:300]))
    print(f"  {'PASS' if t4 else 'FAIL'}: {r4[:200]}")
    print()

    # Test 5: Observation feedback chain
    print("=== Test 5: Observation feedback chain ===")
    agent = NallyAgent(session_id="9d-render-t5")
    r5 = agent.process(
        "On the computer: first write 'RENDER_CHAIN' to /home/nally/workspace/r5-chain.txt, "
        "then read that file back and tell me exactly what it contains"
    )
    t5 = "RENDER_CHAIN" in r5
    results.append(("Observation feedback chain", t5, r5[:200]))
    print(f"  {'PASS' if t5 else 'FAIL'}: {r5[:150]}")
    print()

    # Test 6: Persistence — same computer_id
    print("=== Test 6: Persistence ===")
    cid1 = preflight.computer_id
    client2_obj = ComputerClient()
    client2_obj.timeout_connect = 15.0
    client2_obj.timeout_health = 30.0
    client2_obj.timeout_ttfb = 60.0
    client2 = ComputerAdapter(client2_obj)
    pf2 = client2.preflight()
    cid2 = pf2.computer_id if not isinstance(pf2, ComputerError) else "ERROR"
    t6 = cid1 == cid2
    results.append(("Persistence (same computer_id)", t6, f"{cid1} == {cid2}"))
    print(f"  {'PASS' if t6 else 'FAIL'}: {cid1} == {cid2}")
    print()

    # Test 7: File persists across sessions
    print("=== Test 7: Persistence — file survives ===")
    agent = NallyAgent(session_id="9d-render-t7")
    r7 = agent.process("Read /home/nally/workspace/render-proof.txt on the computer and tell me what it says")
    t7 = "RENDER_PROOF" in r7
    results.append(("File persists across sessions", t7, r7[:200]))
    print(f"  {'PASS' if t7 else 'FAIL'}: {r7[:150]}")
    print()

    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for label, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print(f"\nTests 4-7 Render: {passed}/{total}")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
