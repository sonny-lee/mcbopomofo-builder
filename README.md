# mcbopomofo-builder

macOS dual-architecture (`arm64` / `x86_64`) GitHub Actions builder for [openvanilla/fcitx5-mcbopomofo](https://github.com/openvanilla/fcitx5-mcbopomofo), packaged in the `fcitx5-plugins` split format:

- `mcbopomofo-arm64.tar.bz2`
- `mcbopomofo-x86_64.tar.bz2`
- `mcbopomofo-any.tar.bz2`

Includes static linking for `fmt`, `json-c`, and `icu4c` (verified via `otool -L` to have zero `/opt/homebrew` or `/usr/local` dynamic dependencies) and applies `patches/mcbopomofo-macos-webpanel-fix.patch`.
