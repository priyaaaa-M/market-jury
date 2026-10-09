# Security

- Never commit API keys, broker credentials or `.env` files. `.gitignore` excludes them.
- The engine requires an API key on every route. If `API_KEY` is not set it generates a random one at startup and prints it to the log.
- Bind to `127.0.0.1` unless you put the engine behind HTTPS and a reverse proxy.
- Report issues privately through GitHub security advisories.
