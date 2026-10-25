# Data map (PRD E6)

| Module | Data item | Stored where | Sent to | Kept for | Why |
|---|---|---|---|---|---|
| Repository tooling | Pull-request title, description and diff (public, test data only) | GitHub | DeepSeek API (third-party model provider; not under our control) | Per DeepSeek's retention terms | Automated PR review (`.github/workflows/pr-review.yml`) |
