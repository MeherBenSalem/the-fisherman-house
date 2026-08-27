# Contributing

Thanks for contributing to The Fisherman House.

## Development

1. Fork and clone the repository.
2. Create a branch for your change.
3. Work in the Minecraft version folder that matches your target (`1.20.1/`, `1.21.1/`, `26.1.2/`, or `26.2/`).
4. Shared datapack assets live in `shared/resources/` — update those and copy into each version's `common/src/main/resources/` when changing worldgen or the structure NBT.
5. Build with the JDK required by that version tree (see README).
6. Open a pull request with a short description of what changed and why.

## Coding expectations

- Prefer small, focused changes.
- Do not add mixins unless they are required for a real feature.
- Keep loader entry points thin; put shared logic in `common`.
- Match existing naming: `mod_id` is `fisherman_house`, package is `tn.nightbeam.fishermanhouse`.

## Issues and pull requests

- Use issues for bugs and feature requests.
- PRs should build cleanly for the versions you touch.
- By contributing, you agree that your contributions are licensed under the Apache License 2.0 unless stated otherwise.
