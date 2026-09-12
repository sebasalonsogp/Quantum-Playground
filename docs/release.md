# Release and demo runbook

## Production deployment

| Setting | Value |
| --- | --- |
| Platform | Streamlit Community Cloud |
| App URL | <https://quantum-playground-app.streamlit.app> |
| Repository | <https://github.com/sebasalonsogp/Quantum-Playground> |
| Branch | `main` |
| Entrypoint | `app.py` |
| Python | `3.12` |
| Dependency source | Root `uv.lock` and `pyproject.toml` |
| Secrets | None |
| External system packages | None |

Community Cloud automatically redeploys after a push to `main`. The app is public, stores no user
data, makes no external API calls, and accepts only bounded numeric and enumerated controls.

## Two-minute portfolio demo

1. **0:00–0:20 — Establish the product.** Open the app and identify the experiment selector,
   scientific figure, concise trust signal, and expandable evidence.
2. **0:20–0:45 — Show a validated baseline.** In the infinite well, choose a higher state and point
   out its nodes, exact-energy error, and solver time.
3. **0:45–1:20 — Run the flagship interaction.** Choose **Symmetric double well**, select state 2,
   enable probability density, and note the default split `ΔE₀₁ = 0.068624`.
4. **1:20–1:40 — Make the result memorable.** Set `V₀ = 8.0` and `d = 4.0`; the split falls to
   approximately `0.000758`, or `98.9%` below the default.
5. **1:40–2:00 — Prove the numerics.** Expand **Numerical details**, show the passing residual,
   normalization, and orthogonality checks, then reset the experiment.

## Release checklist

- [ ] GitHub Actions passes on the release commit.
- [ ] A clean clone installs from the committed lockfile, runs all checks, and builds both artifacts.
- [ ] The live app loads over HTTPS without browser console errors.
- [ ] The live flagship journey completes using keyboard-accessible controls.
- [ ] The live app links back to the public repository.
- [ ] The README image, live badge, setup commands, and engineering evidence are current.
- [ ] Repository description, topics, homepage, and release notes are current.
- [ ] No secrets, credentials, personal data, uploads, external API calls, or database are present.
- [ ] The potential composer remains explicitly outside the MVP.

## Operations and rollback

Community Cloud logs are the first diagnostic surface for build or runtime failures. GitHub Actions
is the pre-deployment quality gate, and the live two-minute journey is the post-deployment smoke
test. This portfolio app has no database, migration, background jobs, or persisted user state.

Rollback is source-controlled:

1. Revert the offending commit on `main` and push the revert.
2. Watch the automatic Community Cloud redeploy and its logs.
3. Confirm the app loads, run the flagship journey, and verify the repository link.

If the live app is unavailable while a correction is prepared, the public repository, screenshot,
and reproducible local setup remain the portfolio fallback.
