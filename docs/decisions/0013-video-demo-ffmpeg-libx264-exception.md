# 0013. Video demo: ffmpeg with `libx264` (GPL), one narrow exception

**Date:** 2026-11-22
**Status:** Decided by the guide on 2026-11-22
([comment on PR #129](https://github.com/narenccode/learnops/pull/129#issuecomment-7080514340)).
This record writes the decision down. It is the **licence record for the demo's ffmpeg** that PRD
C-11 asks for; it is not added to `requirements-dev.txt`.
**Requirements:** PRD C-11 (licences), FR-V-03 (in part, by the demo only)
**Contracts touched:** none.

## Context

The Lesson Processor demo (`modules/video/demo/lesson_processor/`, PR #129) calls `ffmpeg` and
`ffprobe` as separate programs. It converts video with the encoder `libx264`. `libx264` is a GPL
encoder, and the Windows build named in the demo README and the `apt` package installed in CI are
typically built with it. PRD C-11 says third-party dependencies, "runtime, development and CI alike",
must have a permissive licence and that no GPL or AGPL is allowed; it does not say whether a program
called as a separate process counts. The Video design (`docs/design/video.md`, Q10) requires an LGPL
build without GPL-only parts for the pipeline.

## Decision

**The demo's use of `libx264` may stay, as one narrow, recorded exception for this demo only.** The
guide does not read C-11 in the demo's favour: this is an explicit exception for PR #129. It goes
beyond the guide's earlier exception of 2026-11-19, which covered only `CLAUDE.md` section 6a.2,
section 7 item 7 and the size rule.

What the record states, as the guide required:

- **Demo only.** The exception covers the Lesson Processor demo and nothing else.
- **ffmpeg runs as a separate program.** It is never linked or imported.
- **Nothing is added to `requirements.txt`** (or to `requirements-dev.txt`) for ffmpeg.
- **Licence status: "ffmpeg with libx264 is GPL; not an approved production build."**

## Conditions

1. This record is the licence record for the demo's ffmpeg. The README note in
   `modules/video/demo/lesson_processor/README.md` stays.
2. The exception **ends when the demo is removed or replaced** by the pipeline that uses the LGPL
   build (design question Q10). It is **not a precedent** for the pipeline or for any other pull request.
3. The pipeline itself still needs an ffmpeg build without GPL parts. That stays a design question
   (`docs/design/video.md`, Q10).

## Not verified

Which ffmpeg build the CI package and the lab image contain. The lab image's `ffmpeg -version` line is
still to be sent to the guide. The guide named a second option, that the demo avoid a GPL encoder; he
did not check whether the demo's ffmpeg can encode H.264 without `libx264`, so what that would cost is
unknown. It was not chosen.
