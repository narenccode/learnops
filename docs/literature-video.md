# Video module: literature survey (Release 0)

**Module:** Video (M4, Student 4: Nagashree V, `vnaags`).
**Requirement:** `docs/GETTING-STARTED.md` (Student 4, "Literature survey for **your** module": at least 6 sources, each opened and verified) and PRD C4.12 "Bloom mapping" (Survey, L2: Indian-English speech recognition, lecture segmentation, summarisation, resumable upload protocols).
**Status:** Draft. **1 of at least 6 sources recorded. The survey is not complete.**

This file is the single consolidated Video-module survey. `docs/GETTING-STARTED.md` allows a survey in `docs/design/<module>.md` §12 or in `docs/literature-<module>.md`; this file uses the second option. Sources are added one at a time, each only after the owner has opened and verified it (`CLAUDE.md` §6a, rule 5: AI tools can invent citations).

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

Topics in C4.12 with no source recorded yet: lecture segmentation, summarisation, resumable upload protocols, and BigBlueButton recordings. Further speech-recognition sources are also still to be added.

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

*Next sources to add (not yet opened or verified; no entries made):* further Indian-English or lecture speech-recognition evidence, a definition of WER and its limits, lecture segmentation, summarisation, resumable upload protocols, and BigBlueButton recordings.
