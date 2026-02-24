# Project D Business Requirements Document (BRD)

Date: February 24, 2026  
Project: Project D — Memory & Learning Application

## 1. Purpose
Project D is a web-based memory and learning application that helps users encode, practice, and retain A–Z knowledge pairs through evidence-based learning techniques. It combines data management with adaptive quiz flows, progress tracking, and retention analytics to maximize learning outcomes.

## 2. Business Objectives
- Enable users to efficiently encode structured knowledge (A–Z categorized pairs).
- Maximize learning retention through evidence-based 3-stage quiz methodology (practice → active recall → alphabetical review).
- Adapt difficulty dynamically based on user performance (harder questions require more correct attempts).
- Track and visualize learning progress with timestamped completion records.
- Provide accessible, intuitive learning experience for non-technical users via browser interface.

## 3. Stakeholders
- Primary End User: Learner seeking to memorize and retain structured knowledge.
- Domain Expert: Creates and curates knowledge lists (ABC pairs).
- Product Owner: Defines learning flows, difficulty adaptation, and UX expectations.
- Administrator: Maintains Google credentials, spreadsheet access, and data persistence.

## 4. Scope
### In Scope
- Knowledge base management: worksheet CRUD operations for organizing learning sets.
- Knowledge pair operations: create, read, update, delete A–Z key/value sets.
- Learning content generation: Google Maps integration for rapid ABC data capture.
- Evidence-based learning flow:
  * Practice Stage: passive review of knowledge pairs (encoding).
  * Quiz Stage: randomized active recall with adaptive difficulty (spaced practice).
  * Final Stage: alphabetical review for retrieval strength (distributed practice).
- Performance analytics: timestamped results tracking, completion history, progress visualization.
- User experience: real-time feedback, progress indicators, review timers, multi-value support per key.

### Out of Scope
- Multi-user/multi-learner support with separate progress tracking.
- Native mobile application (web-responsive only for now).
- Spaced repetition scheduling (fixed 3-stage flow, not interval-based).
- Advanced BI dashboards; analytics limited to Google Sheets native features.
- Gamification (leaderboards, badges, streaks).

## 5. Learning Methodology
Project D is grounded in evidence-based learning science principles:

### Encoding
The Practice stage allows users to passively review knowledge pairs, establishing initial memory traces (encoding phase) without performance pressure.

### Spaced Practice
The 3-stage learning flow (Practice → Quiz → Final) distributes learning over time, leveraging the spacing effect—repeated retrieval at increasing intervals strengthens memory.

### Active Recall
The Quiz stage forces learners to retrieve answers from memory (not just recognize), which strengthens memory traces more than passive review (retrieval strength).

### Adaptive Difficulty
When users answer incorrectly, the system increases the bar for mastery (requires more correct attempts), implementing error-driven learning: learners focus remediation on weaker items.

### Distributed Practice
The Final stage requires alphabetical review—forcing learners to organize and retrieve knowledge in non-random order, building robust, context-independent memory representations.

### Review Timers
45-second review periods after repeated errors promote metacognition and consolidated encoding by enforcing reflection time before re-engagement.

## 6. Functional Requirements
- FR-01: The system shall connect to Google Sheets using service account credentials.
- FR-02: The system shall support selecting the first worksheet when none is configured.
- FR-03: The system shall list all worksheets in the active spreadsheet.
- FR-04: The system shall allow selecting a worksheet by name.
- FR-05: The system shall allow deleting a worksheet.
- FR-06: The system shall allow renaming a worksheet.
- FR-07: The system shall create A–Z keys in the target worksheet and populate values.
- FR-08: The system shall display current A–Z values in read mode.
- FR-09: The system shall update existing key/value pairs.
- FR-10: The system shall clear values while preserving keys.
- FR-11: The system shall provide a practice stage for review.
- FR-12: The system shall provide a randomized quiz stage with correctness checks.
- FR-13: The system shall provide a final alphabetical review stage.
- FR-14: The system shall display quiz completion feedback and indicate result persistence.
- FR-15: The system shall store each completed quiz with timestamp, worksheet name, and status.
- FR-16: The system shall display historical quiz results in a dedicated results view.

## 7. Non-Functional Requirements
- NFR-01: The UI shall be readable and consistently formatted.
- NFR-02: Critical status feedback shall be clearly visible.
- NFR-03: Google Sheets failures shall degrade gracefully with clear messaging.
- NFR-04: Sensitive credentials shall remain outside source control.
- NFR-05: Common operations should complete within reasonable interactive expectations.

## 8. Data Requirements
### ABC Worksheet Data
- Key: Single-letter category (A–Z).
- Value: User-generated or imported text values (multiple per key supported).

### Quiz Results Data (Dedicated Worksheet)
- Timestamp (YYYY-MM-DD HH:MM:SS)
- Worksheet Name
- Status (e.g., Completed)

## 9. Assumptions
- Valid Google service account credentials are provided and spreadsheet is shared.
- Users operate one active worksheet context per session.

## 10. Constraints
- Web-UI-only interaction model.
- Dependency on Google API availability and credential validity.
- Selenium scraping reliability depends on browser/driver compatibility.

## 11. Success Metrics (KPIs)
- Learning engagement: quiz completion rate per week/month.
- Knowledge retention: progression through practice → quiz → final stages per topic.
- User satisfaction: time-to-mastery for new knowledge sets.
- Platform reliability: successful load/save operation rate.
- User experience: error-free quiz flow completion rate.

## 12. Acceptance Criteria
- AC-01: User can create a new knowledge set (worksheet with A–Z pairs) and optionally populate from Google Maps.
- AC-02: User can review, edit, and delete knowledge pairs with persistence to Google Sheets.
- AC-03: User can complete all three learning stages (Practice, Quiz, Final) and receive immediate performance feedback.
- AC-04: Quiz difficulty adapts: incorrect answers trigger review timers and increased required correct attempts.
- AC-05: All quiz completions are logged with timestamp, knowledge set name, and status.
- AC-06: User can view historical quiz performance across all learning sessions.
- AC-07: The app displays current knowledge set and progress context clearly throughout the UX.

## 13. Risks and Mitigations
- Risk: Knowledge set quality impacts learning outcomes and retention.
  - Mitigation: Domain experts review content; periodic audits; incorporate user feedback; learning science review.
- Risk: Adaptive difficulty algorithm too aggressive or too lenient.
  - Mitigation: A/B testing of algorithm parameters; user feedback surveys; tuning of timer thresholds and required-attempt multipliers.
- Risk: Low long-term user engagement and retention.
  - Mitigation: Progress visualization dashboards; optional streak tracking; milestone badges; in-app reminders for spaced practice.
- Risk: Google Sheets performance degradation at scale (>10K knowledge pairs).
  - Mitigation: Database migration path documented; batch read/write optimization; caching strategy for warm data.
- Risk: Data loss or synchronization issues with Google Sheets.
  - Mitigation: Automated backups; transactional error logging; write-validation; rollback mechanisms.
- Risk: Dependency vulnerabilities (Selenium, gspread, streamlit).
  - Mitigation: Regular security audits; dependency scanning; pinned versions in requirements.txt; fallback data sources.
- Risk: Credential exposure.
  - Mitigation: Keep .env and credentials out of source control; restrict access scope.

## 14. Future Enhancements (Optional)
- Spaced repetition scheduling: interval-based review reminders (e.g., Anki-style scheduling).
- Per-user progress tracking and individual learning curves.
- Advanced retention analytics: forgetting curves, confidence scoring, difficulty metrics.
- Export/import to standard flash card formats (Anki, Quizlet).
- Multi-topic support with cross-topic retention tracking.
- Mobile-responsive UI improvements for on-the-go studying.
- Peer/group learning modes with comparative progress dashboards.

---

**Document Owner:** Product Owner / Business Analyst  
**Last Updated:** February 24, 2026  
**Next Review Date:** [To be scheduled after stakeholder feedback]
