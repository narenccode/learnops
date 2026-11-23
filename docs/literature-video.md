# Video module: literature survey (Release 0)

**Module:** Video (M4, Student 4: Nagashree V, `vnaags`).
**Requirement:** `docs/GETTING-STARTED.md` (Student 4, "Literature survey for **your** module": at least 6 sources, each opened and verified) and PRD C4.12 "Bloom mapping" (Survey, L2: Indian-English speech recognition, lecture segmentation, summarisation, resumable upload protocols).
**Status:** Draft. **Owner-verified sources: 13 (S2 and P1 to P12); the requirement of 6 is met.** The survey is still a Draft and is NOT complete in coverage: the gaps listed below (lecture-specific segmentation and summarisation, BigBlueButton `metadata.xml`, WER normalisation) are open. The owner states (2026-11-23) that all twelve entries P1 to P12 were opened and verified; the verification is the owner's statement and covers the facts each entry states.

This file is the single consolidated Video-module survey. `docs/GETTING-STARTED.md` allows a survey in `docs/design/<module>.md` §12 or in `docs/literature-<module>.md`; this file uses the second option. Sources are added one at a time, each only after the owner has opened and verified it (`CLAUDE.md` §6a, rule 5: AI tools can invent citations). AI-researched candidates are kept in a separate "Pending entries" section, labelled PENDING OWNER VERIFICATION, and are not counted.

**How to read an entry.** Each entry separates four kinds of statement:

- **Paper-reported:** what the paper itself states.
- **Authors' interpretation:** the authors' explanations or hypotheses, not shown by controlled experiments in the paper.
- **Audit observation:** something noticed while checking, including discrepancies. Discrepancies are kept, not resolved.
- **UNKNOWN:** the paper or the audit does not supply it. Nothing is filled in from outside the paper.

Published results are not LearnOps results. No LearnOps speech evaluation has been run.

## Sources recorded

| ID | Source | Type | Owner verification |
|---|---|---|---|
| S2 | Javed et al., *Svarah: Evaluating English ASR Systems on Indian Accents* (arXiv 2305.15760 v1) | Research paper (benchmark dataset and evaluation) | Complete: all five PDF pages inspected |
| P1 | Radford et al., *Robust Speech Recognition via Large-Scale Weak Supervision* (arXiv 2212.04356) | Indian-English ASR (model) | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P2 | Bhogale et al., *Vistaar: Diverse Benchmarks and Training Sets for Indian Language ASR* (arXiv 2305.15386) | Indian-language ASR | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P5 | tus resumable upload protocol 1.0.x | Resumable upload | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P9 | W3C, *Web Content Accessibility Guidelines (WCAG) 2.1*, success criterion 1.2.2 *Captions (Prerecorded)* | Captioning accessibility | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P10 | W3C, *WebVTT: The Web Video Text Tracks Format* (Candidate Recommendation Draft, 20 May 2026) | Caption file format (`captions.en.vtt`) | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P3 | Hearst, *Text Tiling: Segmenting Text into Multi-paragraph Subtopic Passages* (Computational Linguistics 23(1), 1997) | Lecture segmentation | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P4 | Atri et al., *See, Hear, Read: Leveraging Multimodality with Guided Attention for Abstractive Text Summarization* (arXiv 2105.09601) | Summarisation | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P6 | IETF Internet-Draft *Resumable Uploads for HTTP* (draft-ietf-httpbis-resumable-upload) | Resumable upload | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P7 | BigBlueButton documentation, recording development page | BigBlueButton recordings | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P8 | BigBlueButton documentation, API page (getRecordings) | BigBlueButton recordings | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P11 | nginx documentation, `client_max_body_size` in `ngx_http_core_module` | Reverse-proxy upload size limit | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |
| P12 | Jurafsky and Martin, *Speech and Language Processing* (3rd ed. draft), chapter 16 *Automatic Speech Recognition* | WER definition (textbook) | Owner opened the source and confirmed the entry matched it (2026-11-23); the verification covers the facts the entry states, not parts it marks as unread |

### Pending entries

None. All twelve AI-researched entries (P1 to P12) were first read by an AI assistant (Claude Code, web fetch, 16 and 22 Nov 2026), not by the owner; the owner then opened each source and confirmed it (2026-11-23). Where an entry still says a part of a page was not read, or a fact is UNKNOWN, the owner has not reported otherwise, so that statement stands.

### Coverage against C4.12 survey topics

| Topic | Verified (owner) | Pending | Gap |
|---|---|---|---|
| Indian-English speech recognition | S2, P1, P2, P12 | none | No source on technical-lecture WER; whether chapter 16 of P12 defines WER and normalisation was not reported, so it is not recorded; no normalisation source |
| Lecture segmentation | P3 | none | P3 is 1997 text segmentation, not lecture video or ASR transcripts; no modern lecture-specific source |
| Summarisation | P4 | none | P4 is conference-talk video; no lecture-transcript summarisation paper read |
| Resumable upload protocols | P5, P6, P11 | none | P11 documents one proxy's limit and its 413 error; still no evidence on browser limits or on real-world robustness |
| BigBlueButton recordings | P7, P8 | none | The owner confirmed on 2026-11-23 that the P7 page does not mention `metadata.xml`, so its format needs another source (P8 or a lab recording) |
| Captioning accessibility and caption format | P9, P10 | none | The entries cover the page headers and the one criterion; the WebVTT cue syntax and the other WCAG criteria were not read |

Summary: 13 owner-verified sources (S2 and P1 to P12); the requirement of 6 is met. The coverage gaps above are still to be addressed.

---

## S2. Svarah: Evaluating English ASR Systems on Indian Accents

### 1. Citation and source

- **Title (as printed):** *Svarah: Evaluating English ASR Systems on Indian Accents*
- **Authors (printed order):** Tahir Javed, Sakshi Joshi, Vignesh Nagarajan, Sai Sundaresan, Janki Nawale, Abhigyan Raman, Kaushal Bhogale, Pratyush Kumar, Mitesh M. Khapra
- **Identifier:** arXiv 2305.15760, **v1**, submitted 25 May 2023
- **Abstract page:** https://arxiv.org/abs/2305.15760
- **PDF:** https://arxiv.org/pdf/2305.15760
- **Venue wording on page 1:** "Submitted to INTERSPEECH". This is a submission statement. It is **not** evidence that the paper was accepted or published at Interspeech, and no publication citation or page range is attributed to it here.

### 2. Objective and contribution

**Paper-reported.** The stated motivation is that existing English speech datasets do not represent Indian speakers with diverse accents well. The authors introduce **Svarah**, an Indian-accented English speech benchmark with speakers across India, varied accents and linguistic backgrounds, and varied speech content, and evaluate open-source and commercial ASR systems on it.

### 3. Dataset characteristics

**Paper-reported.**

| Item | Value |
|---|---|
| Total duration | 9.6 hours |
| Speakers | 117 Indian speakers |
| Native languages | 19 |

**Speech categories and durations (paper-reported):**

| Category | Duration |
|---|---:|
| Read speech | 1.4 hours |
| Extempore | 6.4 hours |
| Everyday-use-case utterances | 1.7 hours |

**Audit observation: duration discrepancy.** The paper reports 9.6 hours overall. The three category durations (1.4 + 6.4 + 1.7) sum to **9.5** hours. Both statements are recorded as printed. They are not reconciled and no rounding explanation is offered.

**Geographic coverage (paper-reported, three different statements).**

| Where | Statement |
|---|---|
| Abstract | 65 geographic locations throughout India |
| Figure 1 caption / introduction | 65 districts across **19** states |
| Section 3 dataset summary | 65 districts in **17** Indian states |

**Audit observation: geographic discrepancy.** The 19-state and 17-state statements disagree, and the abstract uses a different unit ("locations"). None is chosen as correct here.

**UNKNOWN:** gender and age breakdown of the speakers.

### 4. Collection and transcription

**Paper-reported: collection.**

- Platform: Microsoft's open-source crowdsourcing platform **Karya**, used as an Android app.
- Participants register and log in with a mobile number and record their responses in the app.
- The app automatically replays each recording. Participants check background noise and audibility at 50% device volume.
- Four task categories: (1) read speech; (2) questions on topics of interest; (3) questions on domains of interest; (4) prompts on everyday use cases.

**Paper-reported: transcription and quality checks.**

- Transcribers were undergraduate and postgraduate students fluent in English.
- They checked audio quality and whether each response addressed its prompt.
- They segmented recordings into logical segments, typically sentences.
- They used a modified Label Studio workflow and followed the Switchboard corpus transcription guidelines.

**UNKNOWN:** number of prompts per participant; exact number of samples checked during transcription and quality review.

### 5. ASR evaluation methodology

**Paper-reported: systems evaluated.** Six open-source model families and two commercial service families.

| Group | System | Parameters (as stated) |
|---|---|---|
| Open source | Whisper base, medium, large | 74M, 769M, 1550M |
| Open source | Wav2Vec2 Large | 317M |
| Open source | HuBERT Large | 316M |
| Open source | WavLM Large | 300M |
| Open source | Data2Vec Large | 313M |
| Open source | NVIDIA Conformer Large | 120M |
| Commercial | Microsoft Azure Speech-to-Text, en-US and en-IN | not provided |
| Commercial | Google Speech-to-Text, en-US and en-IN | not provided |

**Paper-reported: evaluation sets and metric.**

- Svarah, the Speech Accent Archive native-speaker subset (`SAA_L1`), and LibriSpeech Clean (`Libri` in Table 1).
- Metric: word error rate (WER).
- The authors state that **no external language model** was used with the listed models, because they wanted to evaluate the acoustic models' ability to handle diverse accents. This is not recorded as evidence of greedy decoding.

**Paper-reported: model and training details.**

- **Whisper:** 680K hours of weakly supervised multilingual data, including 438K hours of English. The authors suggest that training-data diversity may help with accent variation.
- **Wav2Vec2, HuBERT, Data2Vec, WavLM (self-supervised):** pretrained on 60K hours of LibriVox and fine-tuned on 960 hours of LibriSpeech, except WavLM, which was fine-tuned on the 100-hour clean LibriSpeech subset. Public Hugging Face versions are mentioned.
- **NVIDIA Conformer Large:** CTC loss; no unsupervised pretraining; trained on 24,500 hours of gold-standard data from 11 sources.
- **Google and Azure:** both US English and Indian English regional variants were evaluated through the providers' SDKs.

**UNKNOWN (not specified in the paper, or not recorded in the audit):**

- exact checkpoint repository IDs and commit hashes
- greedy versus beam decoding, beam width, language-model weights
- Whisper task or prompt settings and temperature
- audio preprocessing, resampling, normalisation and segmentation configuration
- the text-normalisation rules applied before computing WER
- evaluation-library and other software or library versions
- hardware
- commercial provider model versions and internal decoding configurations

### 6. Results and author interpretations

#### 6.1 Table 1: WER on Svarah, SAA_L1 and Libri (paper-reported)

Table 1 reports the WERs of the different models on Svarah, SAA_L1 and Libri. Values are WER as printed. A dash is a dash in the table: no value was printed and none is inferred.

| Model | Parameters | Svarah | SAA_L1 | Libri |
|---|---:|---:|---:|---:|
| Whisper_base | 74M | 13.6 | 2.9 | 4.2 |
| Whisper_medium | 769M | 8.3 | 1.7 | 3.1 |
| Whisper_large | 1550M | 7.2 | 1.6 | 2.7 |
| Wav2Vec2_large | 317M | 24.9 | 3.1 | 1.8 |
| HuBERT_large | 316M | 25.6 | 3.2 | 2.0 |
| WavLM_large | 300M | 33.7 | 9.2 | 3.4 |
| Data2Vec_large | 313M | 24.5 | 2.5 | 1.8 |
| Conformer_large | 120M | 14.6 | 1.1 | 2.1 |
| Azure_US | — | 20.9 | 24.2 | — |
| Azure_IN | — | 21.3 | 30.1 | — |
| Google_US | — | 30.0 | 16.8 | — |
| Google_IN | — | 20.7 | 63.7 | — |

#### 6.2 Table 2: WER by accent and by speech type (paper-reported)

Caption as printed: "Table 2: The WER of different models on different splits of Svarah based on (i) accents and (ii) types of data (Re: read speech, Ex: extempore speech, UC: use cases)."

Column abbreviations: Wlarge = Whisper Large; W2V2 = Wav2Vec2; HuB = HuBERT; D2V = Data2Vec; Clarge = Conformer Large; GIN = Google IN; AzUS = Azure US. Only the top seven models appear in this table, because of space (paper-reported). Accent codes are given as printed; this entry does not expand them. The authors' discussion names Assamese, Bodo and Nepali.

**By accent:**

| Accent code | Wlarge | W2V2 | HuB | D2V | Clarge | GIN | AzUS |
|---|---:|---:|---:|---:|---:|---:|---:|
| ne | 9.8 | 34.4 | 35.2 | 32.6 | 20.5 | 27.5 | 33.1 |
| brx | 11.6 | 29.9 | 30.5 | 29.0 | 18.5 | 26.7 | 38.3 |
| as | 10.1 | 32.3 | 33.8 | 31.6 | 21.4 | 20.6 | 18.1 |
| doi | 8.0 | 29.1 | 28.5 | 26.8 | 16.5 | 21.1 | 21.6 |
| sd | 7.3 | 27.2 | 26.5 | 26.5 | 16.8 | 19.1 | 21.0 |
| ml | 8.1 | 23.7 | 26.5 | 23.0 | 14.7 | 24.9 | 20.4 |
| kn | 6.6 | 27.2 | 27.1 | 27.0 | 14.6 | 17.7 | 14.2 |
| mr | 6.8 | 24.6 | 26.0 | 26.2 | 15.0 | 18.6 | 15.5 |
| bn | 7.6 | 24.1 | 24.8 | 25.1 | 14.1 | 18.5 | 16.6 |
| pa | 6.7 | 22.3 | 22.3 | 22.6 | 13.3 | 17.4 | 25.2 |
| ur | 6.2 | 22.3 | 23.3 | 21.8 | 14.2 | 21.5 | 19.7 |
| te | 7.5 | 23.4 | 23.1 | 22.6 | 14.3 | 18.8 | 17.6 |
| ks | 6.9 | 20.3 | 21.2 | 20.3 | 12.6 | 27.8 | 18.3 |
| kok | 6.4 | 20.1 | 21.3 | 19.7 | 11.9 | 19.2 | 25.3 |
| or | 6.2 | 24.5 | 24.9 | 24.8 | 12.1 | 17.5 | 13.4 |
| guj | 6.0 | 23.3 | 24.0 | 22.6 | 12.7 | 13.1 | 17.8 |
| hi | 5.3 | 20.7 | 20.8 | 20.4 | 10.9 | 19.7 | 21.0 |
| mai | 4.5 | 20.7 | 21.9 | 20.7 | 11.6 | 15.4 | 19.6 |
| ta | 5.3 | 17.8 | 18.8 | 18.6 | 10.7 | 17.4 | 9.9 |

**By speech type** (Re = read speech; Ex = extempore speech; UC = everyday use cases):

| Data type | Wlarge | W2V2 | HuB | D2V | Clarge | GIN | AzUS |
|---|---:|---:|---:|---:|---:|---:|---:|
| Re | 6.2 | 22.8 | 23.3 | 21.7 | 12.6 | 21.3 | 24.0 |
| Ex | 7.4 | 23.4 | 25.3 | 28.0 | 14.0 | 18.4 | 10.1 |
| UC | 11.2 | 34.6 | 35.4 | 33.7 | 23.3 | 19.8 | 15.7 |

#### 6.3 Measured findings (paper-reported)

- A performance gap between Svarah and the native-speaker evaluation sets for all six open-source model families.
- The authors state the Svarah-versus-SAA_L1 gap ranges from 5.65 to 43.03 and the Svarah-versus-LibriSpeech gap from 4.5 to 30.3.
- Whisper medium and large reach single-digit WER on Svarah.
- Whisper is the best-performing family in the authors' comparison, Conformer next. The self-supervised models perform poorly relative to both. The commercial Google and Azure systems perform worse than Whisper and Conformer on Svarah.
- Azure's Svarah results are better than its native-speaker-dataset results. The authors say they cannot explain this because Azure's internal model details are unknown.
- Accent level: the authors' discussion names Assamese, Bodo and Nepali as showing poorer performance. Across-accent standard deviation is reported as 1.8 for Whisper Large and 3.0 for Conformer.
- Speech type: all models except the two commercial models perform better on read and extempore speech than on everyday-use-case speech. Whisper Large's everyday-use-case WER is 11.2. The authors identify named entities (brand names, bank names, food items, document IDs) in those utterances as difficult to recognise with Indian accents.
- Correlation across accents: the authors describe high correlations among the open-source models, higher still among the self-supervised ones, and weaker correlation between commercial and open-source models (Figure 2, below).

**Audit observation: stated gap range versus Table 1.** The stated Svarah-versus-SAA_L1 range does not directly match the Whisper Large subtraction from Table 1 (7.2 − 1.6 = 5.6 percentage points, against the stated 5.65). Using Table 1 as printed, the largest open-source Svarah-minus-SAA_L1 difference is WavLM_large, 33.7 − 9.2 = 24.5, which does not reproduce the stated upper bound of 43.03. The authors' stated range is preserved, and no calculation method is assumed. The paper's own explanation of how the range was computed is not recorded.

#### 6.4 Figure 2

Caption as printed: "Figure 2: Correlation between the WERs of different models across different accents." It is a heatmap of seven systems: Whisper Large, Wav2Vec2, HuBERT, Data2Vec, Conformer, Google en-IN and Azure en-US, with a colour scale of approximately 0.4 to 1.0. Individual correlation coefficients are not printed, so none are reported here. Nothing is derived from the colours.

#### 6.5 Authors' interpretations (hypotheses, not shown by controlled experiments)

- Whisper's diverse weakly supervised training data may help it handle accent variation.
- Conformer's large, diverse gold-standard training set may explain its relatively strong results.
- Pretraining on diverse unlabelled data may be less useful than fine-tuning on diverse labelled data for this task.
- WavLM's weaker performance may be related to its 100-hour fine-tuning subset.
- Large Whisper variants may be hard to deploy in the Indian context because of model size.
- Differences in proprietary training data and model design may explain the low correlation between commercial and open-source models.

The paper does not establish any of these through controlled causal experiments.

### 7. Related datasets and comparison (page 2)

**Paper-reported.** Datasets named: LibriSpeech, Switchboard-1, WSJ-0, WSJ-1, VCTK, VoxPopuli, Mozilla Common Voice, Speech Accent Archive (SAA), Foreign Accented English (FAE), IITM, NPTEL, AccentDB. The paper states that none of the existing datasets has good representation of Indian speakers with diverse accents, and describes Svarah as having more diverse content across domains and use cases, with speakers across India speaking 19 different native languages.

| Dataset | What the paper says (as recorded in the audit) |
|---|---|
| SAA | 59 Indian speakers, 26 minutes, read speech only |
| FAE | Native Hindi speakers, 0.5 hours; native Tamil speakers, 1 hour; the paper says it does not capture India's large linguistic diversity |
| IITM / NPTEL | Named as datasets. The paper says they contain data only from the STEM domain and describes the speakers as professors at premier higher-education institutes in India with good English fluency. Footnote 4 links to the English ASR Challenge website |
| AccentDB | 8 speakers from 4 Indian languages |

**Audit observation: do not over-read IITM/NPTEL.** IITM and NPTEL are named as datasets, not merely institutions. The paper says "STEM domain". It does not establish that the recordings are classroom lectures, professor lectures or lecture videos, and this entry does not infer a lecture format from the description of the speakers.

### 8. Limitations and unknowns

The inspected pages contain **no dedicated limitations heading or subsection.** The following are evidence-based limitations or unknowns:

- Only the top seven models appear in the accent-level comparison, because of space.
- Azure's internal model details are unknown.
- Checkpoint IDs and commit hashes are not given. Decoding, normalisation, preprocessing, software and hardware details are not specified (see §5).
- Individual correlation coefficients are not printed.
- No significance tests or WER confidence intervals are recorded in the inspected pages.
- Per-accent speaker counts and the method for the standard deviations are not recorded.
- No detailed causal analysis is given for the poorer Assamese, Bodo and Nepali results.
- The duration discrepancy (§3), the geographic discrepancy (§3) and the stated-gap-range observation (§6.3) are unresolved.

### 9. Availability and licensing statements

**Paper-reported.** The conclusion says: "Our dataset and all evaluation scripts will be publicly available." The abstract separately says: "Svarah as well as all our code will be publicly available."

These are future-tense statements of intent. They are **promises, not proof** that the dataset, code or scripts were actually released.

On the final inspected page (page 5): no dataset licence statement, no code licence statement, no download URL, no repository URL and no access instructions are printed.

- **Dataset and code licences are not stated in the paper.**
- **Actual release status is not verified in this audit.** No external source was used to check it.

### 10. Relevance to LearnOps Video

- Svarah is an **Indian-accented English ASR benchmark.** It may inform how ASR is evaluated on Indian-accented English, including the reporting of WER per accent and per speech type.
- It is **not** evidence about technical-lecture transcription, classroom recordings, programming or engineering lecture vocabulary, long-form academic lecture video, lecture segmentation, chapter generation or an educational video-processing pipeline. It does not evaluate the LearnOps lecture workflow.
- The published WERs are the authors' 2023 results on their own set and say nothing about WER on LearnOps B8.5 lecture recordings. Those have to be measured by LearnOps, and that has not been done.
- The paper does not specify its WER text normalisation, so its figures should not be compared directly with WER from other sources until normalisation is known.

### 11. Acknowledgements (Section 7 of the paper)

Ministry of Electronics and Information Technology (MeitY), Government of India (supported the work); Centre for Development of Advanced Computing (C-DAC), Pune (supported the work and provided access to GPU nodes on the Param Siddhi Supercomputer); EkStep Foundation and Nilekani Philanthropies (grant support for human resources and cloud resources); the AI4Bharat team (helped connect the researchers to native speakers across India). No individual grant numbers are stated in the audit evidence.

### 12. Selected references from the paper's list (page 5, [1] to [15])

- [1] A. Radford et al., "Robust speech recognition via large-scale weak supervision." CoRR abs/2212.04356, 2022.
- [3] A. Baevski et al., "wav2vec 2.0: A framework for self-supervised learning of speech representations." NeurIPS 2020.
- [4] S. Hollands, D. Blackburn, H. Christensen, "Evaluating the performance of state-of-the-art ASR systems on non-native English using corpora with extensive language background variation." Interspeech 2022.
- [5] A. Gulati et al., "Conformer: Convolution-augmented transformer for speech recognition." Interspeech 2020.
- [12] T. Lander, "CSLU: Foreign Accented English Release 1.2." 2022.
- [13] A. Ahamad, A. Anand, P. Bhargava, "AccentDB: A database of non-native English accents to assist neural speech recognition." LREC 2020.

Also listed: [2] Xiong et al., toward human parity in conversational speech recognition (2017); [6] LibriSpeech (2015); [7] Switchboard (1992); [8] SMS-WSJ (2019); [9] CSTR VCTK (2019); [10] VoxPopuli (2021); [11] Common Voice (2019); [14] crowdsourcing speech data for low-resource languages from low-income workers (2020); [15] IndicSUPERB (2022).

These are references as listed in the paper. They have **not** been opened or verified as separate sources in this survey. SAA and IITM/NPTEL have no separate entry in the paper's reference list.

### 13. Verification record

| Item | Record |
|---|---|
| Source | arXiv 2305.15760 v1 (abstract page and PDF, links in §1) |
| Inspected by | The owner (Student 4), personally |
| PDF length | **Five** PDF-viewer pages; page 5 is the last |
| Abstract and page 1 | Owner-stated verified |
| Pages 2 to 5 | Owner-verified |
| Audit status | **Complete. Owner-verified** (all five PDF pages inspected) |
| Date the owner first opened the paper | **UNKNOWN.** Not separately recorded |
| Extraction discrepancy | An automated text extraction of the PDF produced six pages. This is an extraction artefact only. The PDF itself was visually inspected as five pages |
| Entry prepared | From the owner's audit evidence packet, with AI assistance (Claude Code). A reviewer who wants to spot-check should compare the Table 1 and Table 2 values against the PDF |
| External information | None used. No dataset-card, repository or other external claims are included |

---

# Entries P1 to P12 (all owner-verified, 2026-11-23)

Labels in these entries: **Source-stated** (printed on the page read), **Our interpretation** (AI-assistant reasoning about LearnOps; not published evidence), **NOT PRINTED** (not on the page; not filled in). Quotes are short. Abstracts are paraphrased, not verbatim. Only the entries marked OWNER-VERIFIED say the owner opened the source; the others were read by an AI assistant only.

## P1. Whisper: Robust Speech Recognition via Large-Scale Weak Supervision

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.** Already named in S2's references ([1], listed there as CoRR abs/2212.04356; S2 did not open it separately).

- **Title:** Robust Speech Recognition via Large-Scale Weak Supervision
- **Authors (printed order):** Alec Radford, Jong Wook Kim, Tao Xu, Greg Brockman, Christine McLeavey, Ilya Sutskever
- **Identifier / URL:** arXiv 2212.04356; https://arxiv.org/abs/2212.04356
- **Version/date:** only v1 listed, submitted 6 Dec 2022. **Venue:** NOT PRINTED. **Licence:** the page links the arXiv non-exclusive distribution licence; no code or model licence is printed there.
- **Source-stated:** speech systems trained on 680,000 hours of multilingual, multitask data transfer zero-shot to standard benchmarks, are often competitive with prior supervised results and approach human accuracy and robustness; models and inference code are released.
- **Our interpretation:** the authors' claims are on standard benchmarks. They are not Indian-English lecture results; S2 (verified) is the only evidence here on Indian-accented English, and it evaluated Whisper (WER on Svarah in S2 §6.1).
- **Relevance (interpretation):** informs the candidate-model list for the speech-options decision (`docs/decisions/0002-speech-options.md`, still proposed in an open PR at the time of writing). Model and code licences must be checked at their source before any adoption; this entry does not establish them. All speech calls stay behind `libs/model_interface` (`CLAUDE.md` §2.6).
- **Limits:** no LearnOps WER measured.

## P2. Vistaar: Diverse Benchmarks and Training Sets for Indian Language ASR

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.**

- **Authors (printed order):** Kaushal Santosh Bhogale, Sai Sundaresan, Abhigyan Raman, Tahir Javed, Mitesh M. Khapra, Pratyush Kumar
- **Identifier / URL:** arXiv 2305.15386; https://arxiv.org/abs/2305.15386 (full text read from the HTML version, https://arxiv.org/html/2305.15386v2; the PDF fetch returned no extractable text)
- **Versions:** v1 24 May 2023; v2 2 Aug 2023. **Venue line on page:** "Accepted in INTERSPEECH 2023". **Licence:** arXiv non-exclusive distribution licence (paper text); dataset, code and model licences NOT PRINTED on the pages read.
- **Source-stated:** 59 benchmarks across 12 Indian languages; 3 public and 2 commercial systems evaluated; Whisper fine-tuned on 10.7K hours into IndicWhisper, lowest WER on 39 of 59 benchmarks with an average 4.1 WER reduction; data, code and models stated as open-sourced. NPTEL is described as training data ("conversational speech from classroom lecture recordings of undergraduate and graduate level engineering courses"), 857 hours in its Table 2, and is not among the 59 benchmarks.
- **NOT PRINTED:** any Indian-English test set or accent analysis; WER normalisation; a limitations section (the text does say Indian-language WERs are still large).
- **Our interpretation:** the paper is about Indian languages, not Indian-accented English, so it does not answer the English-lecture question. Its NPTEL note shows that lecture-style engineering speech exists as training data, which is the closest it comes to our domain.
- **Relevance (interpretation):** motivates evaluating per domain and per language rather than trusting headline WER; relevant to the B8.5 lecture set and the caption-WER measure (PRD G-6).
- **Limits:** no English evaluation; results not LearnOps results.

## P3. Hearst: Text Tiling

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.**

- **Title (as printed on the ACL Anthology page):** Text Tiling: Segmenting Text into Multi-paragraph Subtopic Passages
- **Author:** Marti A. Hearst. **Journal:** Computational Linguistics, Volume 23, Number 1, pages 33-64, March 1997 (from the volume title; the Month field is blank). **Publisher:** MIT Press.
- **URL:** https://aclanthology.org/J97-1003/ (ACL Anthology ID J97-1003). **DOI:** NOT PRINTED on that page. **Abstract:** NOT PRINTED there. **Licence:** the page footer says pre-2016 materials are CC BY-NC-SA 3.0.
- **Search-snippet statements (not confirmed on the Anthology page; confirm in the PDF):** the method splits expository text into contiguous multi-paragraph segments using lexical co-occurrence and distribution patterns, and was compared against human judgements of subtopic boundaries on 12 texts.
- **Evaluation section read by the owner (text of section 6.1 pasted 2026-11-23):** judgments were obtained from seven readers for each of 12 magazine articles of 1,800 to 2,500 words (one longer text of 2,932 words was also used) with little structural demarcation; readers marked the paragraph boundaries where the topic changed. The average kappa against the group decision (a gap counts as a boundary when at least three of seven judges marked it) was .647, which the author calls the low end of the acceptable range. Section 6.2 says the evaluation collection is very small, so the results are only a suggestion. This confirms the "12 texts" figure; the lexical co-occurrence description above was not in the pasted part and rests on the search snippet.
- **Our interpretation:** this is text segmentation of written expository text. It says nothing about speech transcripts, ASR errors, or lecture video. A transcript has no paragraphs, so applying it needs sentence or time-window units chosen by us.
- **Relevance (interpretation):** a classic baseline for transcript-based chapter boundaries (PRD C4 chapters). A design document should treat it as a baseline idea only and evaluate on B8.5 with reference chapters.
- **Limits:** 1997; written text; no lecture data.

## P4. See, Hear, Read (AVIATE / FLORAL)

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.**

- **Authors (printed order):** Yash Kumar Atri, Shraman Pramanick, Vikram Goyal, Tanmoy Chakraborty
- **Identifier / URL:** arXiv 2105.09601; https://arxiv.org/abs/2105.09601. **Versions:** v1 20 May 2021; v2 15 Sep 2021. **Comment line:** "Journal paper accepted in Knowledge Based Systems" (volume, pages and DOI NOT PRINTED). **Licence:** CC BY 4.0 (arXiv page).
- **Source-stated (paraphrase):** existing methods use short videos and short summaries; the authors introduce AVIATE, described as a large-scale abstractive summarisation dataset of videos of diverse duration compiled from conference presentations (NDSS, ICML, NeurIPS), with paper abstracts as reference summaries; they propose FLORAL, a multimodal Transformer decoder model, and report ROUGE-L gains of 1.39 on How2 and 2.74 on AVIATE over baselines.
- **Our interpretation:** the videos are conference talks with paper-abstract targets, not classroom lectures; ROUGE gains do not tell us whether a summary is acceptable to a mentor. LearnOps rule: AI output is a draft needing mentor approval (`CLAUDE.md` §2.5).
- **Relevance (interpretation):** shows summarisation of long presentation video is a research task with a multimodal option, but the PRD baseline is transcript-based, so P4 is background only.
- **Not covered:** a Springer article (Benedetto et al., DOI 10.1007/s10639-023-11855-w) surfaced in a search as a closer match on lecture summarisation, but its page redirected to a login and was **not read**. No metadata is recorded. It is a candidate for the owner to open.

## P5. tus resumable upload protocol 1.0.x

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.**

- **URL:** https://tus.io/protocols/resumable-upload (source repository: https://github.com/tus/tus-resumable-upload-protocol)
- **Source-stated:** "Version: 1.0.0 (SemVer)", dated 2016-03-25. Core methods HEAD, PATCH, OPTIONS; headers include Upload-Offset, Upload-Length, Tus-Resumable, Tus-Version, Tus-Extension, Tus-Max-Size. Named extensions: Creation (incl. defer-length), Creation With Upload, Expiration, Checksum, Termination, Concatenation. "Licensed under the MIT license" (repository shows LICENSE.txt); copyright Transloadit Ltd and Contributors 2013-2016. Authors printed: Felix Geisendörfer, Kevin van Zonneveld, Tim Koschützki, Naren Venkataraman, Marius Kleidl; "authored and owned by the tus community".
- **Our interpretation:** the client reads the server's offset with HEAD and resumes with PATCH from that offset; a stable, openly licensed spec. A protocol spec is not evidence of robustness on our network or behind our proxy.
- **Relevance (interpretation):** one candidate for the upload service design (C4 resumable upload, upload robustness in the Bloom "Evaluate" list). The licence applies to the specification; the licence of any server or client library must be checked separately (`CLAUDE.md` §2.10).
- **Limits:** no robustness or proxy-limit measurements.

## P6. IETF Internet-Draft: Resumable Uploads for HTTP

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.** **This is a draft, not a standard.**

- **Title:** Resumable Uploads for HTTP. **Draft name:** draft-ietf-httpbis-resumable-upload.
- **Editors (as printed):** M. Kleidl (Transloadit), G. Zhang (Apple Inc.), L. Pardue (Apple).
- **URLs:** https://datatracker.ietf.org/doc/draft-ietf-httpbis-resumable-upload/ ; https://httpwg.org/http-extensions/draft-ietf-httpbis-resumable-upload.html
- **State when read:** the Datatracker page showed revision -15 dated 2 November 2026, "Active Internet-Draft (httpbis WG)", intended status Proposed Standard, expiring 6 May 2027, no RFC number. The httpwg.org page showed a "-latest" copy labelled published 12 November 2026, expiring 16 May 2027. **Re-checked 2026-11-23:** Datatracker still showed revision -15 (2 November 2026, expiring 6 May 2027); the httpwg.org copy now read "Published 17 November 2026", expiring 21 May 2027, with no changes listed since -15 and no revision number printed. The two pages still disagree; both are recorded, neither is chosen. This will change; re-check before citing.
- **Source-stated:** mechanism for resumable uploads over HTTP. Headers Upload-Offset, Upload-Complete, Upload-Length, Upload-Limit; status code 104 (Upload Resumption Supported); media type application/partial-upload. After interruption the client asks the upload resource for its offset (HEAD) and resumes with PATCH. The Status of This Memo says drafts may be updated, replaced or obsoleted at any time.
- **Our interpretation:** the draft is the standards-track counterpart of tus's idea but is unstable, so a design should not depend on its header names. Licence of the document: NOT PRINTED on the pages read.
- **Relevance (interpretation):** informs the ADR comparing tus with the draft for the upload service. A final decision belongs to the design document and the guide.

## P7. BigBlueButton documentation: recording (development)

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.**

- **URL:** https://docs.bigbluebutton.org/development/recording (header "Version: 4.0"; the page does not say it applies to a single BBB version). Authorship and publication date: NOT PRINTED. Licence: NOT PRINTED in what was read.
- **Source-stated:** lifecycle stages Capture, Archive, Sanity, Process, Publish, Playback. Directories: raw `/var/bigbluebutton/recording/raw/<internal-meeting-id>/`, process and publish under `/var/bigbluebutton/recording/{process,publish}/presentation/<internal-meeting-id>/`, playback under `/var/bigbluebutton/published/presentation/<internal-meeting-id>/`. `events.xml` sits in the raw directory (contains e.g. RecordStatusEvent and ParticipantJoinEvent entries). `processing_time` records processing duration. The "presentation" workflow is the default; a separate "video" workflow can produce a single video file (webm shown in a config example). Recordings are requested with `record=true` on the API `create` call.
- **NOT PRINTED / not seen:** `metadata.xml` was not found in the portion read, so its contents are unverified here. The owner opened the page on 2026-11-23 and confirmed that it does not mention `metadata.xml`; its format must come from another source (P8 or a recording on the lab BigBlueButton). Whether published recording files can be taken as separate audio, webcam and screen tracks is not established.
- **Our interpretation:** BBB output is a pipeline with an event log and a presentation-format playback, so intake probably has to start from published artefacts or the API, not from the raw directory; that is a design question for the owner.
- **Relevance (interpretation):** informs BBB intake (PRD C4 BigBlueButton intake) and the verification of the lab BigBlueButton (the repository's App-C item for recording metadata). Our rule that Moodle and BBB are never modified (`CLAUDE.md` §2.1) means intake can only use BBB's documented outputs and API.
- **Limits:** documents version 4.0 by header; the lab BBB version was not checked here.

## P8. BigBlueButton documentation: API (getRecordings)

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.**

- **URL:** https://docs.bigbluebutton.org/development/api (header "Version: 4.0"; about 155k characters; the last ~15k were not read and the middle was only summarised).
- **Verbatim-read (changelog):** getRecordings gained meta and state filters (1.0); thumbnails and a participants element (1.1); pagination with offset and limit (2.6); totalElements (2.7). The owner pasted the whole "Updates to API in BigBlueButton" section on 2026-11-23 and it matches these four lines. The same section also lists, under 2.2, `getRecordingTextTracks` (list the caption or subtitle files available for a recording) and `putRecordingTextTrack` (upload a caption or subtitle file; a track with the same kind and lang is replaced), and under 1.1 that `updateRecordings` can edit meta parameters. Not used by the pipeline design yet; recorded as page-stated facts.
- **From an extracted summary, not read verbatim (re-check on the page):** parameters meetingID, recordID, state, meta, offset, limit; response with recordID, meetingID, internalMeetingID, name, published, state, startTime, endTime, participants, metadata, playback formats (type, url, processingTime, length) and state values processing, processed, published, unpublished, deleted.
- **Our interpretation:** these fields, if confirmed, would be the documented route to find a finished recording without touching BBB internals.
- **Relevance (interpretation):** feeds the BBB-intake design and the lab verification of recording metadata. Not verified against the lab's BBB.
- **Limits:** partly read; version-dependent.

## P9. WCAG 2.1, success criterion 1.2.2 Captions (Prerecorded)

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.** Page headers and the criterion's text were read by an AI assistant (fetched 2026-11-22); the owner then opened the page.

- **URL:** https://www.w3.org/TR/WCAG21/ (title "Web Content Accessibility Guidelines (WCAG) 2.1"; header "W3C Recommendation 06 May 2025").
- **Read:** success criterion 1.2.2, *Captions (Prerecorded)*, conformance **Level A**. Paraphrase: captions must be provided for prerecorded audio in synchronised media, unless the media is a labelled alternative to text.
- **Our interpretation:** a caption file for every lecture video (`captions.en.vtt`, required by PRD B6.2) is what this criterion expects of a lesson page. Whether Moodle's own player meets the rest of WCAG on the lab sites is not claimed.
- **Relevance (interpretation):** supports why `captions.en.vtt` is a required file. PRD UI-03 names WCAG 2.1 AA for contrast.
- **Limits:** only one criterion read; Level A, not AA; not a statement about caption **accuracy** (that is G-6).

## P10. WebVTT: The Web Video Text Tracks Format

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.** Page header read by an AI assistant (fetched 2026-11-22); the owner then opened the page. The cue syntax was **not** read.

- **URL:** https://www.w3.org/TR/webvtt1/ (header "W3C Candidate Recommendation Draft, 20 May 2026"; a 2019 Candidate Recommendation is listed as the previous version).
- **Our interpretation:** the format of the required file `captions.en.vtt` (PRD B6.2). The page is a Candidate Recommendation Draft, not a final Recommendation.
- **Relevance (interpretation):** the pipeline writes this format from the B5.4 transcript segments; a validator for the file should follow this specification.
- **Limits:** syntax, timestamps and cue settings not read; status is a draft.

## P11. nginx: `client_max_body_size`

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.** The directive's text was read by an AI assistant (fetched 2026-11-22); the owner then opened the page.

- **URL:** https://nginx.org/en/docs/http/ngx_http_core_module.html (directive `client_max_body_size`, contexts http, server, location).
- **Read:** the default is `1m`; a request body above the configured size gets the **413 (Request Entity Too Large)** error; the page notes that browsers cannot display this error correctly; `0` disables the check.
- **Our interpretation:** an example of the proxy limit the PRD means by "below a 100 MB proxy limit" (FR-V-01, chunk size 90 MB). It shows why one large upload request fails behind a default proxy and why chunking is needed.
- **Relevance (interpretation):** supports the chunked, resumable upload design. It is one product's documentation; the PRD's 100 MB is the project's assumption, not nginx's default.
- **Limits:** one proxy; says nothing about browsers or about resumable-upload robustness.

## P12. Jurafsky and Martin, Speech and Language Processing, chapter 16

**Status: OWNER-VERIFIED (2026-11-23): the owner opened the source and confirmed the entry matched it.**

- **URL:** https://web.stanford.edu/~jurafsky/slp3/ (page header "Speech and Language Processing (3rd ed. draft)", release dated 19 August 2026; the contents list "16: Automatic Speech Recognition").
- **Not read:** the chapter itself. **UNKNOWN:** whether and how it defines word error rate and its normalisation; this must be checked by opening the chapter.
- **Our interpretation:** a candidate textbook source for the WER definition the survey still lacks.
- **Relevance (interpretation):** would support the WER procedure in `docs/decisions/0002-speech-options.md` section 7.3 and `libs/speech_eval`.
- **Limits:** a draft edition; nothing in this entry is a result about Indian English.

---

# Remaining gaps and risks

1. **Verification:** all twelve entries P1 to P12 are owner-verified (owner's statement, 2026-11-23), on top of S2. Anything an entry still says was not read stays unread unless the owner reports otherwise.
2. **Indian-English lecture ASR:** no source covers technical-lecture WER; P2 covers Indian languages, not English. A WER definition and normalisation source is missing.
3. **Lecture segmentation and summarisation:** only an old text-segmentation paper (P3) and a conference-talk summarisation paper (P4). The unread Springer article is a lead only.
4. **Resumable upload:** specifications and one proxy's documented limit (P11); no evidence on browser limits or robustness (the PRD's "upload robustness" evaluation is LearnOps's own to measure).
5. **BBB:** `metadata.xml` (not on the P7 page, owner-confirmed), separate tracks and the lab BBB version are unverified.
6. **Not yet covered:** privacy and consent literature for lecture recordings (an Indian data-protection source could not be fetched on 2026-11-22), and Moodle-side video embedding (the Moodle documentation site refused automated requests). Captioning accessibility is covered only by P9 and P10, at header level.

*Next sources to add (owner-verified entries only count once the owner has opened them):* the sources above, plus the gap areas.
