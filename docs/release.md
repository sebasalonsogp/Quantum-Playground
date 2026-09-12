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

- [x] GitHub Actions passes on the release commit.
- [x] A clean clone installs from the committed lockfile, runs all checks, and builds both artifacts.
- [x] The live app loads over HTTPS without browser console errors.
- [x] The live flagship journey completes using keyboard-accessible controls.
- [x] The live app links back to the public repository.
- [x] The README image, live badge, setup commands, and engineering evidence are current.
- [x] Repository description, topics, homepage, and release notes are current.
- [x] No secrets, credentials, personal data, uploads, external API calls, or database are present.
- [x] The potential composer remains explicitly outside the MVP.

## Release evidence

The release candidate was verified on Windows with CPython 3.12 on 2026-09-11:

- GitHub Actions installed the locked environment, checked formatting and lint, ran the test suite,
  and built the package successfully.
- A separate clone from the public repository repeated those gates: `128` tests passed and both the
  source distribution and wheel were created. Its documented Streamlit command started the app and
  returned `ok` from `/_stcore/health`.
- A real-browser production smoke test loaded the HTTPS deployment, completed the double-well
  journey, showed all three diagnostics passing, reset cleanly, and reported no console errors.
- A dependency audit reported no known vulnerabilities. Targeted repository and history scans found
  no committed credentials, private keys, environment files, or Streamlit secrets.

## Product-brief evaluation

| Success criterion | Release evidence |
| --- | --- |
| Understand the project within 30 seconds | The title, one-sentence purpose, experiment selector, coordinated figure, and concise trust signal are visible before the expandable technical detail. |
| Produce a meaningful result within 90 seconds | The flagship path takes seven direct actions; it was also completed comfortably inside the scripted two-minute explanation. |
| Create an obvious double-well change | Raising `V0` to `8.0` and `d` to `4.0` reduced the lowest-state split from `0.068624` to `0.000758` (`-98.9%`). |
| Demonstrate grid convergence | Infinite-well refinement produced observed convergence orders `1.99999` and `2.00000`. |
| Meet numerical tolerances | Residual, normalization, and orthogonality checks pass in tests and are exposed in the app. |
| Keep local solves near 250 ms or less | Representative solver medians are `1.9-6.4 ms`, with an `11.0 ms` measured maximum. |
| Keep hosted interactions under one second | The production flagship solve completed in approximately `108 ms`; local uncached app reruns had a `62.9 ms` median. |
| Test numerical and critical UI behavior deterministically | The release suite contains `128` passing tests across contracts, numerics, figures, caching, failures, and Streamlit flows. |

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
