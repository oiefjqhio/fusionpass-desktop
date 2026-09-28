# Fusion Pass desktop

Fork of [NuvioDesktop](https://github.com/NuvioMedia/NuvioDesktop) (GPL-3.0) with the Fusion Pass branding and lock-down.

- `python3 fusionpass/rebrand.py` after every upstream merge (`git merge upstream/Dev`), then commit. Idempotent; exits on an anchor upstream moved.
- Icons: `fusionpass/brand/render-desktop.mjs` then `pack-icons.py` (out/desktop/app.ico, app.icns).
- Build: Actions > "Build Desktop Release", mode `build-only`, target `all` (unsigned DMG/MSI, Linux packages as artifacts).
- Secret `NUVIO_DESKTOP_LOCAL_PROPERTIES_BASE64` = base64 of `fusionpass/app.properties` plus `TMDB_API_KEY=...`.
