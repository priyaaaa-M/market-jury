# Security

- Never commit API keys, broker credentials or `.env` files. `.gitignore` excludes them.
- The engine requires an API key on every route. If `API_KEY` is not set it generates a random one at startup and prints it to the log.
- Bind to `127.0.0.1` unless you put the engine behind HTTPS and a reverse proxy.
- Report issues privately through GitHub security advisories.

## Phase 2 verification limits (9 October 2026)
Production dependencies returned no npm audit findings after the React Router update. The development/build Tailwind 3 dependency tree still reports braces/chokidar/micromatch/postcss advisories; npm proposes a breaking Tailwind 4 migration. Do not expose development servers or process untrusted CSS/glob input. This dependency migration remains open, not silently auto-forced. This is not a security audit or production-ready hosting claim. API-key auth is single-instance, not a multi-user permission model. Public aggregate scoreboard is opt-in and must be isolated behind a reviewed reverse proxy. Never expose the authenticated API with a shared key.
