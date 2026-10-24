# Contracts folder — read before changing anything here

Files here are **shared contracts** between modules (PRD Part B). They are frozen after Release 0.

- Never edit a schema or example as part of other work.
- Every change goes through `/contract-change` (PRD §B.0): additive and optional only after Release 0; schema + examples + PRD text + every affected module's tests in **one** pull request; approved by every affected owner and the guide.
- A breaking change needs a new version file (`*.v2.schema.json`), never an edit to `v1`.
- Every schema has at least one valid example in `examples/`, and CI validates all examples.

| Contract | File | Owner |
|---|---|---|
| B1 Course package | `course-package.v1.schema.json` | Student 1 |
| B2 Course model | `course-model.v1.schema.json` | Student 2 |
| B3 LTI launch | `lti-launch.v1.md` (claims and role mapping) | Student 2 |
| B4 Web-services usage | `moodle-ws.v1.md` (functions and capabilities) | Student 3 |
| B5 Model and speech interface | `model-interface.v1.schema.json` | Student 3 |
| B6 Lesson manifest and paths | `lesson-manifest.v1.schema.json` | Student 4 |
| B7 H5P practice output | `h5p-practice.v1.md` | Student 1 |
| B8 Test data sets | `testdata/README.md` | Students 1, 3, 4 |
