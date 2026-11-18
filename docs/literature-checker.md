# Literature Survey — Course Checker, Role Tests and Integration Harness

**Module:** checker (M2)  
**Owner:** @shraddha0103  
**Peer reviewer:** @Akshita21-09  
**Release:** Release 0 research supporting Release 1 implementation  
**Prepared:** 19 November 2026  
**Status:** Literature survey — source verification completed for the references listed below

## 1. Purpose and scope

This survey reviews the technical and research literature relevant to LearnOps Module 2 (M2): Course Checker, role tests and integration harness. The review is organised around the module's responsibilities in PRD §C2: (1) build the B2 course model from Moodle `.mbz` backups and Course Studio packages; (2) evaluate availability and completion rules and identify unreachable learning items; (3) apply CK-01–CK-13 quality rules; (4) test role-based access through Playwright; (5) integrate build, check, restore and browser tests across Moodle 4.5 and 5.3; and (6) provide the mentor-facing checker entry point through LTI 1.3.

The sources comprise official Moodle documentation, the 1EdTech standards, official Playwright documentation and peer-reviewed research. Official technical documentation is treated as the authority for platform behaviour and protocol requirements. Research papers are used to frame course-quality evaluation and quality-assurance practice; they are not treated as specifications for LearnOps.

## 2. Review method

Sources were located through targeted searches of official Moodle, 1EdTech and Playwright documentation sites and scholarly journal/publisher records. Each source below was opened and checked for its title, publisher or issuing body, publication/version information where available, and content relevant to M2. The review prioritised current Moodle 4.5/5.3 documentation and primary standards over secondary tutorials. Access date for all web sources: **19 November 2026**.

This is a focused engineering literature survey, not a systematic review: no exhaustive database search, formal inclusion/exclusion protocol or meta-analysis was performed. The two research papers provide evidence about course-quality evaluation; the official technical sources provide normative or implementation guidance.

## 3. Thematic review

### 3.1 Moodle course backups, XML and restoration

Moodle's 5.3 Backup API describes course backup as a plan composed of tasks and steps. At activity-module level, backup implementations define the data structure to be exported, connect nested elements into a hierarchy and identify their data sources. The documentation also explains why internal course links require transformation during backup and restoration: a URL referring to the original Moodle site's activity identifier may not remain valid after the course is restored elsewhere. The corresponding Restore API describes a restore plan made up of tasks and steps, including parsing plugin XML and restoring plugin data. These APIs establish that backup and restore are structured Moodle processes rather than simple copies of database rows [1, 2].

Moodle's user documentation describes the `.mbz` file as a course backup package. The backup workflow lets the creator select course components and activity types, and can include or omit user-related information. Moodle's 5.3 documentation also identifies `moodle_backup.xml` as containing backup information/settings and documents supported setting levels (`root`, `course`, `section`, `activity`) [3, 4]. The practical implication for M2 is that a parser must inspect the archive manifest and XML rather than assume every backup contains the same optional records or user data.

The documentation does **not** establish a complete, version-independent XML schema for every activity type and plugin. Moodle's own backup architecture allows activity modules to contribute their own backup steps and XML structures [1]. Therefore, M2 should parse only the in-scope structures needed by B2 and CK-01–CK-13, preserve unknown/unsupported activity types as “not checked” where required by PRD §C2.8, and test representative backups produced by both Moodle 4.5 and 5.3. The parser should reject malformed or unsafe archives with a clear error; it should not infer that an unfamiliar XML node is invalid course design.

Restoration is a separate verification concern. The restore API documentation explains how Moodle reconstructs plugin data from backup files, but it does not prove the PRD's specific assumption that a sections-only backup can be merged into an existing course while preserving protected items. That remains an explicit Release 0 lab verification item. M2 should therefore treat successful parsing and successful restoration as different outcomes in the integration report [2].

### 3.2 Moodle web services and course/activity retrieval

Moodle's External Services documentation describes a web-service framework for external systems and points developers to two complementary sources: the general developer API documentation and the API documentation exposed by each live Moodle site under Site administration → Server → Web services. This distinction matters because the functions enabled on a particular installation depend on its configuration and service definition [5].

The PRD's B4 contract names course lookup and course-content/enrolment functions, including `core_course_get_courses_by_field`, `core_course_get_contents` and `core_enrol_get_enrolled_users`. The literature supports using Moodle's supported web-service interface rather than querying Moodle's database directly. It does not, by itself, prove that every named function is enabled with the required parameters and capabilities on both project lab versions. Those details must be checked against the live API documentation and the dedicated service account on Moodle 4.5 and 5.3. This is consistent with PRD Appendix C's Release 0 verification requirement [5].

For M2, the web-service adapter should have a narrow, explicit function allow-list. Tests should verify the exact parameters, response fields, service capability requirements and error behaviour against both lab instances. A function's existence in Moodle core is not equivalent to permission for the LearnOps service account to call it.

### 3.3 Course quality, availability and completion

McInnes et al. (2024) conducted a scoping review that identified and analysed 75 instruments used to evaluate online-course design in higher education. The authors group course-quality criteria into five broad domains: learning design; assessment and evaluation; usability and accessibility; social interaction; and technology. They argue that quality instruments can support staff capability development, not merely compliance checking [6]. This provides a research basis for treating a course checker as a structured quality-assurance aid, while recognising that a rule catalogue cannot fully judge pedagogical quality.

Zimmerman et al. (2020) analysed 5,436 online-course reviews from 360 institutions and examined relationships between faculty development, course design and informal reviews and formal inter-institutional review outcomes. The study highlights that publishing standards alone does not guarantee that they are implemented consistently [7]. For M2, this supports combining explicit rule definitions with repeatable tests, documented findings and human review. It does not establish that automated rules can replace a mentor's judgement.

Abid et al. (2024) propose a feature-based framework for comparing learning-management systems across multiple categories, including platform architecture, administration/reporting, academic support, content management, learner support and technical support [8]. Its scope is LMS-level comparison, not validation of individual Moodle courses. Its relevance is therefore contextual: course quality and LMS capability are related but distinct evaluation levels. M2 should not claim to measure overall LMS quality.

Moodle's 5.3 Availability API states that availability controls access to activities and sections, including restrictions based on dates and grades. It also explains that Moodle evaluates whether a user can access an activity using contextual information and that visibility can depend on both hidden status and availability conditions [9]. Moodle 4.5 user documentation lists restriction conditions such as activity completion, date, grade, group/grouping and user profile fields, and notes the dependency on completion tracking for completion-based restrictions [10]. Activity completion is a separate mechanism: completion may be based on viewing, a grade or a learner marking an item complete [11].

These sources have a direct impact on FR-C-02. A course-path simulator cannot model availability as a simple visible/hidden Boolean. It must distinguish the existence of an activity from its accessibility for a particular learner state, and must account for completion prerequisites and compound restrictions. Where a condition type or Moodle-specific behaviour is not supported by the simulator, the checker should report the case as unsupported/not checked rather than claim that the activity is unreachable. The PRD's availability JSON representation should remain the source format; M2 should not invent a replacement representation.

### 3.4 LTI 1.3 architecture, identity and security

The 1EdTech LTI Core Specification 1.3 defines the resource-link launch flow and the `LtiResourceLinkRequest` message. Launches carry claims that describe the issuer, user, context, resource link and deployment. The specification states that deployment identifiers distinguish platform-tool deployments and that user and context identifiers are scoped to the issuer and/or deployment [12]. Its role vocabulary distinguishes system, institution and context roles, and recommends use of the standard role URIs rather than relying on deprecated simple-name forms [12].

The 1EdTech Security Framework defines the shared security approach used by 1EdTech specifications, including OpenID Connect launch flow, ID-token validation, message signing, key management and protection against login CSRF [13]. For LearnOps, this means the LTI gateway must validate the launch as a security protocol, not merely decode a JWT and trust its contents. The issuer, audience, signature/key, nonce, expiry, deployment identity and expected message type must be checked before creating an application session.

A relevant contract-review point emerged when comparing the standard with the current PRD B3 claims table: the standard launch includes an issuer (`iss`) claim, and the user subject (`sub`) is scoped to that issuer. The B3 contract/session identity should therefore preserve issuer context when binding a user to a course session; using `sub` alone risks collisions across Moodle platforms. The current PRD's B3 claim list should be reconciled with the specification before the contract is treated as final. This survey records the discrepancy; it does not change the PRD or contract.

The PRD's policy that Learner launches are refused in the baseline is a LearnOps product decision, not a limitation imposed by LTI 1.3. LTI defines Learner as a context role [12]. LearnOps must apply its own role-mapping and authorisation rules after successful protocol validation. The gateway should fail closed for unknown or unsupported roles and bind the resulting session to the validated platform, deployment, user and course context.

### 3.5 Playwright and role-based browser testing

Playwright's Python authentication guide recommends isolated browser contexts and reuse of authenticated state to avoid repeated login flows. It explicitly warns that saved browser state can contain cookies and headers capable of impersonating a user, and should not be committed to source control [14]. The locator guide recommends user-facing locators such as role, label and text locators, and describes their auto-waiting/retry behaviour [15]. Playwright's Python test documentation recommends its pytest integration for end-to-end testing and supports running tests across browser configurations [16].

These capabilities fit FR-C-06 and FR-C-07. M2 can use separate fixtures or storage states for the five PRD roles, and data-driven YAML expectations to state which pages/actions each role may or may not access. Assertions should cover both positive access and negative access. Accessible, user-facing locators are preferable to brittle CSS/XPath selectors where practical. Authentication state must be generated from synthetic lab accounts, excluded from version control and never copied into test reports.

Playwright verifies the behaviour of the browser-visible application in a particular environment; it does not prove that every Moodle permission configuration is correct in all deployments. The role matrix must therefore be executed against the project's two Moodle versions and all three PRD screen profiles. A passing test on one version or viewport cannot be generalised to the entire matrix.

### 3.6 Integration and cross-version verification

The sources collectively show that M2 spans several independent interfaces: backup files, Moodle's web-service API, Moodle's availability/completion model, LTI launch security and browser-visible role behaviour. None of the sources provides a ready-made end-to-end checker for this combination. The integration harness is consequently a LearnOps-specific contribution: it should coordinate the build, offline parse/check, restore, role tests and available module smoke tests while preserving the distinction between a completed step, a failed step and a blocked step.

The PRD's acceptance criteria provide the measurable evaluation method: detect all planted errors in B8.3 without false errors on B8.2; pass the required five-role × three-screen-profile × two-Moodle-version matrix, including negative checks; and execute the integration path from a clean state with one consolidated report. These are project-defined acceptance criteria, not outcomes established by the literature.

## 4. Evidence summary

| Source | Type and date/version | Main evidence used | M2 relevance |
|---|---|---|---|
| [1] Moodle Backup API | Official developer documentation, Moodle 5.3; page last updated 13 Apr 2026 | Backup plans, tasks/steps, XML structure and activity-specific backup contributions | FR-C-01; parser boundaries |
| [2] Moodle Restore API | Official developer documentation, Moodle 5.3; page last updated 13 Apr 2026 | Restore plans, tasks/steps and plugin XML restoration | FR-C-08; restore verification |
| [3] Moodle Course backup | Official user documentation, Moodle 5.1 | Backup selection and optional course/user data | Input variability and test fixtures |
| [4] Moodle backup setting-level error guidance | Official Moodle 5.3 documentation | `moodle_backup.xml` and supported setting levels | Archive/XML validation |
| [5] Moodle External Services | Official developer documentation, Moodle 5.3; page last updated 13 Apr 2026 | External API framework and site-specific live API documentation | B4 adapter and capability verification |
| [6] McInnes et al. | Peer-reviewed scoping review, 2024 | 75 course-quality instruments and five quality domains | CK catalogue scope and limitations |
| [7] Zimmerman et al. | Peer-reviewed research article, 2020 | Analysis of 5,436 course reviews across 360 institutions | Quality assurance and review practice |
| [8] Abid et al. | Peer-reviewed open-access research article, 2024 | Feature-based LMS evaluation framework | Context for distinguishing LMS from course evaluation |
| [9] Moodle Availability API | Official developer documentation, Moodle 5.3; page last updated 13 Apr 2026 | User-dependent activity/section access and availability conditions | FR-C-02 |
| [10] Moodle Restrict access settings | Official user documentation, Moodle 4.5 | Date, grade, group, profile and completion restrictions | FR-C-02; version-specific tests |
| [11] Moodle Activity completion | Official user documentation, Moodle 5.2 | Viewing, grade and manual completion criteria | FR-C-02; completion evaluator |
| [12] 1EdTech LTI Core Specification | Official standards specification, version 1.3, issued 16 Apr 2019 | Launch request, issuer, subject, context, deployment and roles | B3; FR-C-09 |
| [13] 1EdTech Security Framework | Official standards specification, version 1.0, issued 15 May 2019 | OIDC, ID-token validation, signatures and key management | B3 security |
| [14] Playwright Python Authentication | Official framework documentation; accessed 19 Nov 2026 | Isolated contexts, reusable auth state and secret handling | FR-C-06/07 |
| [15] Playwright Python Locators | Official framework documentation; accessed 19 Nov 2026 | Accessible locators, auto-waiting and retryability | Stable role tests |
| [16] Playwright Python Test runner | Official framework documentation; accessed 19 Nov 2026 | pytest integration and browser test execution | FR-C-06; CI |

## 5. Strongest sources for M2

1. **Moodle Backup API [1] and Restore API [2]:** primary technical sources for the Moodle backup/restore lifecycle. They are more authoritative than third-party descriptions of the `.mbz` format, although they do not define a complete stable schema for all plugin XML.
2. **Moodle Availability API [9]:** primary source for why access evaluation depends on user context and multiple conditions; directly informs the path simulator.
3. **1EdTech LTI Core Specification [12] and Security Framework [13]:** normative sources for launch message structure and validation. These should take precedence over informal LTI implementation examples.
4. **McInnes et al. [6]:** the strongest broad research source for course-quality dimensions because it reviews 75 instruments rather than proposing a single institution's checklist.
5. **Playwright authentication and locator documentation [14, 15]:** primary implementation guidance for safe, repeatable browser tests. These are framework docs, not empirical evidence that a particular role matrix is correct.

## 6. Research gaps and implications

- **No universal Moodle backup schema for all plugins:** Moodle's extensible backup design means activity/plugin XML can vary. Implement a bounded parser, maintain versioned fixtures from Moodle 4.5 and 5.3, and make unsupported activity types visible in reports.
- **Cross-version compatibility must be measured locally:** documentation alone cannot prove that the exact backup structures, web-service functions, capabilities or restore-merge behaviour match the LearnOps lab. Capture test results from both versions in Release 0.
- **Course-quality instruments include human and pedagogical dimensions:** the research literature covers learning design, accessibility, interaction and assessment, but these cannot all be inferred reliably from a backup. CK-01–CK-13 should be described as deterministic structural/logic checks, not a complete judgement of teaching quality.
- **Availability evaluation is state-dependent:** a static parser cannot establish learner reachability without an explicit learner-state model and supported condition semantics. Unknown condition types must not silently pass.
- **LTI identity needs issuer-aware binding:** ensure B3 records and validates `iss` and does not bind sessions on `sub` alone. Confirm the PRD claims table and B3 contract align with the standard.
- **Role tests are environment-specific:** use fixed synthetic accounts and test the full PRD matrix. Keep authentication state out of Git and distinguish blocked tests from passing tests.
- **No source validates the LearnOps-specific acceptance thresholds:** the 100% planted-error detection target, zero false errors on B8.2, and full role/version/profile matrix must be demonstrated through B8 fixtures and lab execution.

## 7. Conclusion

The reviewed literature supports a modular M2 design: parse Moodle backups into the B2 normalised model; evaluate only explicitly supported availability and completion semantics; apply a deterministic rule catalogue; validate Moodle access through the supported web-service interface; secure the mentor entry point according to LTI 1.3 and its security framework; and test actual user-visible permissions with Playwright. The literature also establishes important limits: Moodle backup structures are extensible, course quality is broader than deterministic rules, and browser tests are only as representative as their fixtures and environments.

The implementation evidence must therefore come from LearnOps' own B8.2/B8.3 fixtures and the Moodle 4.5/5.3 lab. The literature informs the design and test strategy; it does not substitute for the project's acceptance tests.

## 8. References

All URLs below were opened and checked on **19 November 2026**.

1. Moodle. (2026). *Backup API* (Moodle 5.3 developer documentation). Moodle Developer Resources. https://moodledev.io/docs/5.3/apis/subsystems/backup
2. Moodle. (2026). *Restore API* (Moodle 5.3 developer documentation). Moodle Developer Resources. https://moodledev.io/docs/5.3/apis/subsystems/backup/restore
3. Moodle. (2025). *Course backup* (Moodle 5.1 user documentation). MoodleDocs. https://docs.moodle.org/501/en/Backup_restore
4. Moodle. (2026). *error/moodle/wrong_setting_level_moodle_backup_xml_file* (Moodle 5.3 documentation). MoodleDocs. https://docs.moodle.org/503/en/error/moodle/wrong_setting_level_moodle_backup_xml_file
5. Moodle. (2026). *External Services* (Moodle 5.3 developer documentation). Moodle Developer Resources. https://moodledev.io/docs/5.3/apis/subsystems/external
6. McInnes, R., Hobson, J. E., Johnson, K. L., Cramp, J., Aitchison, C., & Baldock, K. L. (2024). Online course quality evaluation instruments: A scoping review. *Australasian Journal of Educational Technology, 40*(2), 55–75. https://doi.org/10.14742/ajet.8978
7. Zimmerman, W., Altman, B., Simunich, B., Shattuck, K., & Burch, B. (2020). Evaluating online course quality: A study on implementation of course quality standards. *Online Learning, 24*(4), 147–163. https://doi.org/10.24059/olj.v24i4.2325
8. Abid, A., Tufail, A. H., Ahmed Salem, O. M., Nawaz, N. A., Farooq, U., Abid, I., & Ishaq, K. (2024). An evaluation framework and comparative analysis of the widely used learning management systems. *PLOS ONE, 19*(12), e0311111. https://doi.org/10.1371/journal.pone.0311111
9. Moodle. (2026). *Availability API* (Moodle 5.3 developer documentation). Moodle Developer Resources. https://moodledev.io/docs/5.3/apis/subsystems/availability
10. Moodle. (2025). *Restrict access settings* (Moodle 4.5 user documentation). MoodleDocs. https://docs.moodle.org/405/en/Conditional_activities_settings
11. Moodle. (2025). *Activity completion* (Moodle 5.2 user documentation). MoodleDocs. https://docs.moodle.org/502/en/Activity_completion
12. 1EdTech Consortium. (2019). *Learning Tools Interoperability Core Specification 1.3* (Document version 3; issued 16 April 2019). https://www.imsglobal.org/spec/lti/v1p3/
13. 1EdTech Consortium. (2019). *1EdTech Security Framework 1.0* (issued 15 May 2019). https://www.imsglobal.org/spec/security/v1p0/
14. Microsoft. (n.d.). *Authentication* (Playwright for Python documentation). https://playwright.dev/python/docs/auth
15. Microsoft. (n.d.). *Locators* (Playwright for Python documentation). https://playwright.dev/python/docs/locators
16. Microsoft. (n.d.). *Introduction and test runners* (Playwright for Python documentation). https://playwright.dev/python/docs/intro
