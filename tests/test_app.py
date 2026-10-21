import json

import pytest
from fastapi.testclient import TestClient

import app as service

client = TestClient(service.app)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, lines=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self._lines = lines or []
        self.text = text

    def json(self):
        return self._payload

    def iter_lines(self):
        return iter(self._lines)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


REPO = {
    "full_name": "acme/shop",
    "stargazers_count": 3,
    "forks_count": 1,
    "language": "JavaScript",
    "topics": ["mern"],
}


def fake_github(calls):
    def get(url, headers=None, timeout=None):
        calls.append((url, timeout))
        if url.endswith("/Dockerfile"):
            return FakeResponse(200)
        return FakeResponse(200, REPO)

    return get


def stream(*chunks):
    return [json.dumps({"response": c}).encode() for c in chunks]


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com/acme/shop",
        "https://github.com/acme/shop/",
        "https://github.com/acme/shop.git",
    ],
)
def test_fetch_metadata_parses_urls(monkeypatch, url):
    calls = []
    monkeypatch.setattr(service.requests, "get", fake_github(calls))
    meta = service.fetch_metadata(url, "token")
    assert calls[0][0] == "https://api.github.com/repos/acme/shop"
    assert meta == {
        "name": "acme/shop",
        "stars": 3,
        "language": "JavaScript",
        "forks": 1,
        "has_dockerfile": True,
        "topics": ["mern"],
    }


def test_fetch_metadata_keeps_dots_in_repo_names(monkeypatch):
    calls = []
    monkeypatch.setattr(service.requests, "get", fake_github(calls))
    service.fetch_metadata("https://github.com/acme/acme.github.io", "token")
    assert calls[0][0].endswith("/acme/acme.github.io")


def test_github_calls_have_a_timeout(monkeypatch):
    calls = []
    monkeypatch.setattr(service.requests, "get", fake_github(calls))
    service.fetch_metadata("https://github.com/acme/shop", "token")
    assert all(timeout for _, timeout in calls)


def test_fetch_metadata_surfaces_github_errors(monkeypatch):
    monkeypatch.setattr(
        service.requests, "get", lambda *a, **k: FakeResponse(404, text="Not Found")
    )
    with pytest.raises(service.HTTPException) as err:
        service.fetch_metadata("https://github.com/acme/missing", "token")
    assert err.value.status_code == 404


def test_parse_response_reads_labelled_output():
    text = "Recommendation: Kubernetes\nReasoning: Several services\nscale independently."
    assert service.parse_response(text) == (
        "Kubernetes",
        "Several services scale independently.",
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Kubernetes fits a microservice stack.", "Kubernetes"),
        ("A single VM is enough here.", "VM"),
        ("Use a virtual machine.", "VM"),
        ("The environment is simple.", ""),
    ],
)
def test_parse_response_fallback(text, expected):
    assert service.parse_response(text)[0] == expected


def test_suggest_end_to_end(monkeypatch):
    monkeypatch.setattr(service.requests, "get", fake_github([]))
    sent = {}

    def post(url, json=None, stream=None, timeout=None):
        sent.update(url=url, model=json["model"], prompt=json["prompt"])
        return FakeResponse(lines=stream_lines)

    stream_lines = stream("Recommendation: VM\n", "Reasoning: One small app.")
    monkeypatch.setattr(service.requests, "post", post)

    res = client.post(
        "/suggest",
        json={
            "frontend": "https://github.com/acme/web",
            "backends": ["https://github.com/acme/api"],
            "token": "t",
        },
    )
    assert res.status_code == 200
    assert res.json() == {"recommendation": "VM", "reasoning": "One small app."}
    assert sent["url"] == f"{service.OLLAMA_URL}/api/generate"
    assert sent["prompt"].count("Repo ") == 2


def test_suggest_validates_input():
    assert client.post("/suggest", json={"frontend": "x"}).status_code == 422
