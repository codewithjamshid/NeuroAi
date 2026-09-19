"""Observability: provider_calls sink (startup hook) + GET /observability/provider-calls."""

from app.modules.observability import sink  # noqa: F401  (registers the startup/shutdown hooks)
