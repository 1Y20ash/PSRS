# Security and data-integrity controls

PSRS is a local research prototype, not a certified operational system.

- Use synthetic demand, fictional locations, and generated disruption assumptions only. Never add real military inventories, facilities, routes, schedules, or operational details.
- The SQLite import reads only items, locations, inventory events, and historical demand. It never opens the evaluation-only ground-truth file.
- SQLite foreign keys and checks constrain identifiers, coordinates, event types, and non-negative quantities.
- Flask request bodies are size-limited and responses include defensive security headers. Review the Content Security Policy whenever browser dependencies change.
- Configure PSRS_SECRET_KEY with a random secret before enabling session-dependent features. Never commit .env.
- Enable PSRS_COOKIE_SECURE=true behind HTTPS. Set PSRS_TRUSTED_HOSTS for a known deployment.
- Forecast and routing parameters are validated; hard plan constraints are checked separately from the objective score.
- Run pytest and inspect GitHub Actions on the exact commit before reporting verification.
- No claim of defence-grade readiness, certification, or operational suitability is made.
