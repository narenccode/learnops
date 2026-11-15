# Data map (PRD E6)

| Module | Data item | Stored where | Sent to | Kept for | Why |
|---|---|---|---|---|---|
| Repository tooling | Pull-request title, description and diff (public, test data only) | GitHub | DeepSeek API (third-party model provider; not under our control) | Per DeepSeek's retention terms | Automated PR review (`.github/workflows/pr-review.yml`) |
| Video pipeline (M4) | Uploader's LTI `sub` (lesson manifest `source.uploaded_by`, PRD B6.3): a pseudonymous identifier, personal data that LTI provides (SEC-06) | The manifest (`lesson.json`) inside the published lesson folder, in the media store (B6.2, FR-V-12) | No third party; read by the LearnOps modules that read the B6.3 manifest | Kept with that folder; the folder is never deleted automatically; the CLI removes lessons older than a configured age only after confirmation, default off (FR-V-15); on reprocessing the previous outputs stay until the new ones are complete (FR-V-11), and their later removal is not specified | Records which LTI user uploaded the lesson's source (B6.3 `source`) |
