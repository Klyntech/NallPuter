"""9D Render validation — all 7 tests against Render-hosted NallPuter.

Runs against https://nallputer.onrender.com (production Render deployment).
"""
import sys
import os

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
    # Override config to point to Render
    os.environ["NALLPUTER_URL"] = RENDER_URL
    os.environ["NALLPUTER_TOKEN"] = RENDER_TOKEN
    os.environ["NALLPUTER_STARTUP_GRACE_MS"] = "60000"

    client_obj = ComputerClient()
    # Render free tier needs longer timeouts (cold start + spin-up)
    client_obj.timeout_connect = 15.0
    client_obj.timeout_health = 30.0
    client_obj.timeout_ttfb = 60.0
    client = ComputerAdapter(client_obj)
    preflight = client.preflight()
    if isinstance(preflight, ComputerError):
        print(f"FAIL: preflight failed: {preflight.code} - {preflight.message}")
        return 1
    if not preflight.ready:
        print(f"FAIL: preflight not ready: {preflight.reason}")
        return 1

    print(f"NallPuter: {preflight.computer_id} at {RENDER_URL}")
    print(f"Uptime: {preflight.health.uptime_sec}s, Sync: {preflight.health.sync_state}")
    print()

    registry.set_computer_adapter(client)
    load_all_tools()

    results = []

    # Test 1: Simple exec via process()
    print("=== Test 1: Simple exec via process() ===")
    agent = NallyAgent(session_id="9d-render-t1")
    r1 = agent.process("Run 'echo hello-from-render' on the computer and tell me the output")
    t1 = "hello-from-render" in r1
    results.append(("Simple exec via process()", t1, r1[:200]))
    print(f"  {'PASS' if t1 else 'FAIL'}: {r1[:150]}")
    print()

    # Test 2: Write file via process()
    print("=== Test 2: Write file via process() ===")
    agent = NallyAgent(session_id="9d-render-t2")
    r2 = agent.process("Write the word RENDER_PROOF to a file called /home/nally/workspace/render-proof.txt on the computer")
    t2 = "RENDER_PROOF" in r2 or "render-proof" in r2.lower() or "wrote" in r2.lower()
    results.append(("Write file via process()", t2, r2[:200]))
    print(f"  {'PASS' if t2 else 'FAIL'}: {r2[:150]}")
    print()

    # Test 3: Read file via process()
    print("=== Test 3: Read file from NallPuter ===")
    agent = NallyAgent(session_id="9d-render-t3")
    r3 = agent.process("Read the file /home/nally/workspace/render-proof.txt on the computer and tell me what it says")
    t3 = "RENDER_PROOF" in r3
    results.append(("Read file from NallPuter", t3, r3[:200]))
    print(f"  {'PASS' if t3 else 'FAIL'}: {r3[:150]}")
    print()

    # Test 4: Planning path (COMPLEX)
    print("=== Test 4: Planning path (COMPLEX) ===")
    agent = NallyAgent(session_id="9d-render-t4")
    r4 = agent.process(
        "Write the numbers 1 through 3 to separate files named "
        "/home/nally/workspace/r4_num1.txt through r4_num3.txt on the computer. "
        "Then read all 3 files back and tell me the sum."
    )
    t4 = "6" in r4 and ("r4_num" in r4.lower() or "written" in r4.lower() or "file" in r4.lower())
    results.append(("Planning path (COMPLEX)", t4, r4[:300]))
    print(f"  {'PASS' if t4 else 'FAIL'}: {r4[:200]}")
    print()

    # Test 5: Observation feedback chain
    print("=== Test 5: Observation feedback chain ===")
    agent = NallyAgent(session_id="9d-render-t5")
    r5 = agent.process(
        "On the computer: first write 'CHAIN_TEST' to /home/nally/workspace/r5-chain.txt, "
        "then read that file back and tell me exactly what it contains"
    )
    t5 = "CHAIN_TEST" in r5
    results.append(("Observation feedback chain", t5, r5[:200]))
    print(f"  {'PASS' if t5 else 'FAIL'}: {r5[:150]}")
    print()

    # Test 6: Persistence — same computer_id across adapter instances
    print("=== Test 6: Persistence ===")
    cid1 = preflight.computer_id
    client2 = ComputerAdapter(ComputerClient())
    pf2 = client2.preflight()
    cid2 = pf2.computer_id
    t6 = cid1 == cid2
    results.append(("Persistence (same computer_id)", t6, f"{cid1} == {cid2}"))
    print(f"  {'PASS' if t6 else 'FAIL'}: {cid1} == {cid2}")
    print()

    # Test 7: File persists across agent sessions
    print("=== Test 7: Persistence — file survives ===")
    agent = NallyAgent(session_id="9d-render-t7")
    r7 = agent.process("Read /home/nally/workspace/render-proof.txt on the computer and tell me what it says")
    t7 = "RENDER_PROOF" in r7
    results.append(("File persists across sessions", t7, r7[:200]))
    print(f"  {'PASS' if t7 else 'FAIL'}: {r7[:150]}")
    print()

    # Summary
    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    for label, ok, detail in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print(f"\n9D Render validation: {passed}/{total}")

    if passed == total:
        print("\nNALLY has a real computer on Render.")
    else:
        print("\nSome tests failed. Check details above.")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
