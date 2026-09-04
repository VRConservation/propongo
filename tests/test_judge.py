import os
import shutil
import tempfile

import app.models as models
import app.judge as judge
from app.main import create_app
from app.models import Proposal


_orig_proposals_dir = models.PROPOSALS_DIR
_orig_env = None
_test_dir = None


def setup_function():
    global _orig_env, _test_dir
    _orig_env = dict(os.environ)
    _test_dir = tempfile.mkdtemp()
    models.PROPOSALS_DIR = _test_dir


def teardown_function():
    global _orig_env, _test_dir
    models.PROPOSALS_DIR = _orig_proposals_dir
    os.environ.clear()
    os.environ.update(_orig_env)
    _orig_env = None
    if _test_dir and os.path.exists(_test_dir):
        shutil.rmtree(_test_dir)
    _test_dir = None


def _client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _fake_raw_score(score=4):
    return {
        "score": score,
        "rationale": "Solid, specific answer.",
        "strengths": ["Clear activities", "Named outcomes"],
        "gaps": ["Doesn't say how success is measured"],
    }


def test_score_scope_section_persists_and_returns_result(monkeypatch):
    monkeypatch.setattr(judge, "_call_ollama", lambda system, user: _fake_raw_score())
    monkeypatch.setattr(judge.Config, "OLLAMA_MODEL", "llama3.1")

    p = Proposal(title="Judge Test")
    p.scope = "We will do great things."
    p.save()

    client = _client()
    resp = client.post(f"/api/section/{p.id}/scope/score", json={"model": "ollama"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["score"] == 4
    assert data["model"] == "ollama/llama3.1"
    assert data["gaps"] == ["Doesn't say how success is measured"]

    reloaded = Proposal.load(p.id)
    assert reloaded.judging["scope"]["score"] == 4


def test_score_custom_section_by_id(monkeypatch):
    monkeypatch.setattr(judge, "_call_ollama", lambda system, user: _fake_raw_score(score=2))

    p = Proposal(title="Custom Section Judge Test")
    p.custom_sections = [{"id": "sec-1", "title": "Impact", "content": "We will have impact.", "order": 0}]
    p.save()

    client = _client()
    resp = client.post(f"/api/section/{p.id}/sec-1/score", json={"model": "ollama"})
    assert resp.status_code == 200
    assert resp.get_json()["score"] == 2

    reloaded = Proposal.load(p.id)
    assert reloaded.judging["sec-1"]["score"] == 2


def test_score_missing_proposal_returns_404():
    client = _client()
    resp = client.post("/api/section/nonexistent/scope/score", json={"model": "ollama"})
    assert resp.status_code == 404


def test_score_missing_section_returns_404():
    p = Proposal(title="No Sections")
    p.save()

    client = _client()
    resp = client.post(f"/api/section/{p.id}/not-a-real-section/score", json={"model": "ollama"})
    assert resp.status_code == 404


def test_score_sonnet_without_api_key_returns_clear_error(monkeypatch):
    monkeypatch.setattr(judge.Config, "ANTHROPIC_API_KEY", "")

    p = Proposal(title="No Key Test")
    p.scope = "Some scope text."
    p.save()

    client = _client()
    resp = client.post(f"/api/section/{p.id}/scope/score", json={"model": "sonnet"})
    assert resp.status_code == 400
    assert "ANTHROPIC_API_KEY" in resp.get_json()["error"]


def test_score_ollama_unreachable_returns_clear_error(monkeypatch):
    import urllib.error

    def _raise(*args, **kwargs):
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(judge.urllib.request, "urlopen", _raise)

    p = Proposal(title="Ollama Unreachable Test")
    p.scope = "Some scope text."
    p.save()

    client = _client()
    resp = client.post(f"/api/section/{p.id}/scope/score", json={"model": "ollama"})
    assert resp.status_code == 400
    assert "Ollama" in resp.get_json()["error"]


def test_score_ollama_model_not_pulled_returns_clear_error(monkeypatch):
    import io
    import urllib.error

    def _raise(*args, **kwargs):
        raise urllib.error.HTTPError(
            "http://localhost:11434/api/chat", 404, "Not Found", {},
            io.BytesIO(b'{"error":"model \\"llama3.1\\" not found, try pulling it first"}'),
        )

    monkeypatch.setattr(judge.urllib.request, "urlopen", _raise)

    p = Proposal(title="Ollama Model Missing Test")
    p.scope = "Some scope text."
    p.save()

    client = _client()
    resp = client.post(f"/api/section/{p.id}/scope/score", json={"model": "ollama"})
    assert resp.status_code == 400
    assert "ollama pull" in resp.get_json()["error"]


def test_deleting_custom_section_clears_its_judging_entry(monkeypatch):
    monkeypatch.setattr(judge, "_call_ollama", lambda system, user: _fake_raw_score())

    p = Proposal(title="Delete Cleans Judging")
    p.custom_sections = [{"id": "sec-1", "title": "Impact", "content": "Some content.", "order": 0}]
    p.save()

    client = _client()
    score_resp = client.post(f"/api/section/{p.id}/sec-1/score", json={"model": "ollama"})
    assert score_resp.status_code == 200
    assert Proposal.load(p.id).judging.get("sec-1") is not None

    del_resp = client.delete(f"/api/section/{p.id}/sec-1")
    assert del_resp.status_code == 200
    assert Proposal.load(p.id).judging.get("sec-1") is None


def test_score_uses_rfp_specific_criteria_for_tagged_custom_section(monkeypatch):
    import app.judge_criteria as judge_criteria

    monkeypatch.setitem(
        judge_criteria.RFP_CRITERIA,
        ("cal-fire-wpb-2025", "cal-fire-wpb-2025-bg"),
        "1 = no wood products experience.\n5 = specific named wood products projects.",
    )

    captured = {}

    def _fake_call(system_prompt, user_prompt):
        captured["system_prompt"] = system_prompt
        return _fake_raw_score()

    monkeypatch.setattr(judge, "_call_ollama", _fake_call)

    p = Proposal(title="RFP Tagged Section Test")
    p.custom_sections = [{
        "id": "sec-1",
        "title": "Project Background",
        "content": "We do forestry work.",
        "order": 0,
        "rfp_template_id": "cal-fire-wpb-2025",
        "rfp_section_id": "cal-fire-wpb-2025-bg",
    }]
    p.save()

    client = _client()
    resp = client.post(f"/api/section/{p.id}/sec-1/score", json={"model": "ollama"})
    assert resp.status_code == 200
    assert "wood products" in captured["system_prompt"]


def test_get_criteria_falls_back_to_generic_default():
    import app.judge_criteria as judge_criteria

    assert judge_criteria.get_criteria("scope", None) == judge_criteria.SECTION_CRITERIA["scope"]
    assert judge_criteria.get_criteria("sec-1", None) == judge_criteria.SECTION_CRITERIA["custom"]
    assert judge_criteria.get_criteria("sec-1", ("unknown-template", "unknown-section")) == (
        judge_criteria.SECTION_CRITERIA["custom"]
    )


def test_normalize_result_clamps_out_of_range_score():
    result = judge._normalize_result({"score": 9, "rationale": "x", "strengths": [], "gaps": []})
    assert result["score"] == 5


def test_normalize_result_rejects_missing_score():
    import pytest

    with pytest.raises(judge.JudgeError):
        judge._normalize_result({"rationale": "x"})
