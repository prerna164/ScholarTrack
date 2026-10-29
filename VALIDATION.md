# Validation

- Python 3.12: six integration tests passed.
- Fresh virtual environment installed from requirements-dev.txt: six tests passed.
- Seeded database: 30 projects, 10 ongoing, 10 completed, 10 planned.
- All six page routes and the CSS asset returned HTTP 200 through the application test client.
- Dashboard counts matched seeded records.
- Browser screenshots and visual QA were blocked by a failed Chromium download. Capture script included.
- GitHub push was not performed; no repository destination or publishing client was available.
- Dependency warning: current Starlette warns that its httpx TestClient integration is deprecated. It still passes; adapt the development test transport when upgrading dependencies.
