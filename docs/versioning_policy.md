# Versioning Policy

Effective date: 2026-03-12

Valkyrie Ballistics uses semantic versioning: MAJOR.MINOR.PATCH

## 1. MAJOR versions
Incremented for breaking changes, such as:
- Database schema changes that require migration.
- Removed or fundamentally changed workflows.
- Behavior changes that alter results or outputs.

## 2. MINOR versions
Incremented for new features and improvements that remain backward
compatible.

## 3. PATCH versions
Incremented for bug fixes, performance improvements, and small
adjustments that do not change behavior or data formats.

## 4. Pre-release builds
Pre-release builds may use tags such as alpha, beta, or rc. These builds
are for testing and may change without notice.

## 5. Deprecation policy
Features may be marked as deprecated in a minor release and removed in
the next major release. Deprecations are noted in release notes.

## 6. Release notes
Each release should include:
- Version number.
- Summary of changes.
- Known issues and migration notes.
