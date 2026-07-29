# Bumpversion changes
Write release notes in changelog.md

1. push any changes

2. in the terminal:
`bump2version patch`   # 1.0.0 → 1.0.1  (bug fixes)
`bump2version minor`   # 1.0.0 → 1.1.0  (new features)
`bump2version major`   # 1.0.0 → 2.0.0  (breaking changes)

3. push and push tags
`git push && git push --tags`