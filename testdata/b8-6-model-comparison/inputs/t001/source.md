# Input t001: "Why caches work" (fictional lecture transcript), PROVISIONAL

- **What:** a fictional transcript of a short technical lecture (about 4 minutes, 15 segments), used as the input for the B8.6 `chapters` and `summary` items.
- **Source:** written for this project by Student 3. There is no recording, no real lecturer and no real course content. The text is invented.
- **Shape:** the B5.4 transcript shape (`segments[{start, end, text, words[{start, end, word}]}]`, `meta{provider, model, duration_s, latency_ms, cost_estimate}`). Times are seconds from the start of the audio.
- **How the times were made:** segment times are hand-written. Word times are spread evenly inside each segment, a synthetic rule and not a speech model's output. They are good enough for chapter and summary inputs, not for caption-timing tests.
- **Edge cases on purpose:** segment 3 (47–52 s) is a pause with `text: ""` and `words: []`. Segment 9 (140–156 s) has text but `words: []`, as when a provider returns no word timings. Both are valid under B5.4 (decision record 0001 in PR #25).
- **`meta`:** `provider: fake`, `model: hand-written-fixture`, `latency_ms: 0`, `cost_estimate: 0.0`. No model produced this. `fake` is the B5 test-only provider value. The values are placeholders, not measurements.
- **Status:** PROVISIONAL. The chapter and summary inputs are still to be agreed with Student 4 (design Q12). This file is not part of B8.5 (Student 4's real lectures).
- **Licence:** open decision (see the set README).
