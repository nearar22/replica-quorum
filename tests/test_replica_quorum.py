import json
import sys
import time

CONTRACT = "contracts/replica_quorum.py"
ARTIFACT_URL = "https://artifact.example.org/build-42"
METHOD_URL = "https://protocol.example.net/reproduce-42"
REPORT_A = "https://lab-a.example.com/report-42"
REPORT_B = "https://lab-b.example.net/report-42"
ARTIFACT = "Build 42 artifact manifest. Artifact reference: model-echo-42. Expected deterministic checksum after execution: 7ac9. Package digest is fixed for this study."
METHOD = "Reproduction protocol 42. Execute model-echo-42 with seed 17 in Python 3.13. Compare the resulting checksum with expected checksum 7ac9. Record environment and output."
TEXT_A = "Lab A reproduction report. Tested artifact: model-echo-42. Followed protocol: seed 17 in Python 3.13. Environment: Windows 11, Python 3.13. Result: checksum 7ac9 was reproduced exactly."
TEXT_B = "Lab B reproduction report. Tested artifact: model-echo-42. Followed protocol: seed 17 in Python 3.13. Environment: Ubuntu 24.04, Python 3.13. Result: checksum 7ac9 was reproduced exactly."
CHARLIE = bytes.fromhex("33" * 20)
OUTSIDER = bytes.fromhex("44" * 20)


def addr(value):
    if hasattr(value, "as_hex"):
        return value.as_hex
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    return str(value)


def observation(lab="A", outcome="SUPPORTS"):
    environment = "Environment: Windows 11, Python 3.13" if lab == "A" else "Environment: Ubuntu 24.04, Python 3.13"
    return json.dumps({"outcome": outcome, "artifact_quote": "Tested artifact: model-echo-42", "method_quote": "Followed protocol: seed 17 in Python 3.13", "environment_quote": environment, "result_quote": "Result: checksum 7ac9 was reproduced exactly"})


def enable_consensus(contract, monkeypatch, comparator=None):
    module = sys.modules[contract.__class__.__module__]
    monkeypatch.setattr(module.gl.eq_principle, "strict_eq", lambda fn: fn())
    monkeypatch.setattr(module.gl.eq_principle, "prompt_comparative", comparator or (lambda fn, *_args, **_kwargs: fn()))


def mock_open(vm, artifact=ARTIFACT):
    vm.mock_web(ARTIFACT_URL, {"method": "GET", "status": 200, "body": artifact})
    vm.mock_web(METHOD_URL, {"method": "GET", "status": 200, "body": METHOD})


def mock_report(vm, url, content, artifact=ARTIFACT):
    mock_open(vm, artifact)
    vm.mock_web(url, {"method": "GET", "status": 200, "body": content})


def open_study(contract, vm, alice, bob, study_id="echo-check"):
    vm.sender = alice; mock_open(vm)
    result = contract.open_study(study_id, "Echo checksum replication", "The model-echo-42 artifact produces checksum 7ac9 when protocol 42 is followed.", ARTIFACT_URL, METHOD_URL, json.dumps([addr(bob), addr(CHARLIE)]), 2, int(time.time()) + 3600)
    vm.clear_mocks()
    return result


def test_contract_loads(direct_deploy):
    assert direct_deploy(CONTRACT) is not None


def test_open_freezes_sources_and_rejects_duplicate_identity(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); open_study(contract, direct_vm, direct_alice, direct_bob)
    study = contract.get_study("echo-check")
    assert len(study["artifact_receipt"]["sha256"]) == 64 and len(study["method_receipt"]["sha256"]) == 64
    direct_vm.sender = direct_alice; mock_open(direct_vm)
    with direct_vm.expect_revert("already exists"):
        contract.open_study("echo-check", "Again", "A duplicate study should never replace frozen receipts.", ARTIFACT_URL, METHOD_URL, json.dumps([addr(direct_bob), addr(CHARLIE)]), 2, int(time.time()) + 3600)


def test_two_authorized_reports_reproduce_and_finalize_permissionlessly(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); open_study(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob; mock_report(direct_vm, REPORT_A, TEXT_A)
    first = contract.submit_report("echo-check", REPORT_A, observation("A")); direct_vm.clear_mocks()
    assert first["supports"] == 1 and first["ready_to_finalize"] is False
    direct_vm.sender = CHARLIE; mock_report(direct_vm, REPORT_B, TEXT_B)
    second = contract.submit_report("echo-check", REPORT_B, observation("B")); direct_vm.clear_mocks()
    assert second["supports"] == 2 and second["ready_to_finalize"] is True
    direct_vm.sender = OUTSIDER
    final = contract.finalize_study("echo-check")
    assert final["status"] == "REPRODUCED" and final["result"]["reports"] == 2


def test_unauthorized_and_duplicate_reviewer_are_rejected(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); open_study(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("authorized reviewer"):
        contract.submit_report("echo-check", REPORT_A, observation("A"))
    direct_vm.sender = direct_bob; mock_report(direct_vm, REPORT_A, TEXT_A)
    contract.submit_report("echo-check", REPORT_A, observation("A")); direct_vm.clear_mocks()
    with direct_vm.expect_revert("already submitted"):
        contract.submit_report("echo-check", "https://another.example.org/report", observation("A"))


def test_distinct_report_hosts_are_enforced(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); open_study(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob; mock_report(direct_vm, REPORT_A, TEXT_A); contract.submit_report("echo-check", REPORT_A, observation("A")); direct_vm.clear_mocks()
    direct_vm.sender = CHARLIE
    with direct_vm.expect_revert("distinct source hosts"):
        contract.submit_report("echo-check", "https://lab-a.example.com/second-report", observation("B"))


def test_forged_quote_fails_closed(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); open_study(contract, direct_vm, direct_alice, direct_bob)
    forged = json.loads(observation("A")); forged["result_quote"] = "Result: checksum 9999 was reproduced"
    direct_vm.sender = direct_bob; mock_report(direct_vm, REPORT_A, TEXT_A)
    with direct_vm.expect_revert("quote is absent"):
        contract.submit_report("echo-check", REPORT_A, json.dumps(forged))


def test_changed_frozen_artifact_is_rejected(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); open_study(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob; mock_report(direct_vm, REPORT_A, TEXT_A, ARTIFACT + " Mutated after registration.")
    with direct_vm.expect_revert("has changed"):
        contract.submit_report("echo-check", REPORT_A, observation("A"))


def test_comparator_cannot_swap_outcome_or_quotes(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT)
    def replace(fn, *_args, **_kwargs):
        row = json.loads(fn()); row["outcome"] = "INCONCLUSIVE"; return json.dumps(row)
    enable_consensus(contract, monkeypatch, replace); open_study(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = direct_bob; mock_report(direct_vm, REPORT_A, TEXT_A)
    with direct_vm.expect_revert("changed a stored observation"):
        contract.submit_report("echo-check", REPORT_A, observation("A"))


def test_finalize_waits_for_quorum_and_empty_cancel_is_owner_only(direct_vm, direct_deploy, direct_alice, direct_bob, monkeypatch):
    contract = direct_deploy(CONTRACT); enable_consensus(contract, monkeypatch); open_study(contract, direct_vm, direct_alice, direct_bob)
    direct_vm.sender = OUTSIDER
    with direct_vm.expect_revert("Quorum is not ready"):
        contract.finalize_study("echo-check")
    with direct_vm.expect_revert("Only the owner"):
        contract.cancel_empty_study("echo-check")
    direct_vm.sender = direct_alice; contract.cancel_empty_study("echo-check")
    assert contract.get_study("echo-check")["status"] == "CANCELLED"
