# Project D Business Requirements Document (BRD)

Date: February 23, 2026  
Project: Project D CLI (Google Sheets + Quiz Workflow)

## 1. Purpose
Project D provides a menu-driven CLI application to create, maintain, and quiz A–Z key/value knowledge sets, with persistent storage in Google Sheets and quiz completion tracking.

## 2. Business Objectives
- Reduce manual effort for building and maintaining categorized knowledge lists.
- Improve user recall through a guided 3-stage quiz flow.
- Provide historical visibility of quiz completions for accountability and review.
- Keep operations simple for non-technical users via numbered menu actions.

## 3. Stakeholders
- Primary End User: Learner/operator using the CLI.
- Product Owner: Defines workflows, quiz behavior, and UX expectations.
- Administrator: Maintains Google credentials and spreadsheet access.

## 4. Scope
### In Scope
- Worksheet management (list, select, delete, rename).
- ABC data operations (create, read, update, delete values).
- Quiz flow with Practice, Quiz, and Final (alphabetical review) stages.
- Quiz results persistence and reporting via dedicated worksheet.
- Terminal UX enhancements (centering, section headings, color coding).

### Out of Scope
- Multi-user login and role-based permissions.
- Web/mobile interface.
- Drive-native automatic document generation.
- Advanced BI dashboards outside Google Sheets.

## 5. Functional Requirements
- FR-01: The system shall connect to Google Sheets using service account credentials.
- FR-02: The system shall support selecting the first worksheet when none is configured.
- FR-03: The system shall list all worksheets in the active spreadsheet.
- FR-04: The system shall allow selecting a worksheet by number or exact name.
- FR-05: The system shall allow deleting a worksheet.
- FR-06: The system shall allow renaming a worksheet.
- FR-07: The system shall create A–Z keys in the target worksheet and populate values.
- FR-08: The system shall display current A–Z values in read mode.
- FR-09: The system shall update existing key/value pairs.
- FR-10: The system shall clear values while preserving keys.
- FR-11: The system shall provide a practice stage showing key/value pairs one at a time.
- FR-12: The system shall provide a randomized quiz stage with correctness checks.
- FR-13: The system shall provide a final alphabetical review stage.
- FR-14: The system shall display quiz completion feedback and indicate result persistence.
- FR-15: The system shall store each completed quiz with timestamp, worksheet name, and status.
- FR-16: The system shall display historical quiz results in a dedicated menu option.

## 6. Non-Functional Requirements
- NFR-01: Interface text and prompts shall be readable and consistently formatted.
- NFR-02: Critical status feedback shall use visual color cues.
- NFR-03: Google Sheets failures shall degrade gracefully with clear user messaging.
- NFR-04: Sensitive credentials shall remain outside source control.
- NFR-05: Common menu operations should complete within interactive CLI expectations.

## 7. Data Requirements
### ABC Worksheet Data
- Key: Single-letter category (`A`–`Z`).
- Value: User-generated or imported text value.

### Quiz Results Data (Dedicated Worksheet)
- Timestamp (`YYYY-MM-DD HH:MM:SS`)
- Worksheet Name
- Status (e.g., `Completed`)

## 8. Assumptions
- Valid Google service account credentials are provided and spreadsheet is shared.
- Terminal supports ANSI rendering for color and clear-screen behavior.
- Users operate one active worksheet context per session.

## 9. Constraints
- CLI-only interaction model.
- Dependency on Google API availability and credential validity.
- Selenium scraping reliability depends on browser/driver compatibility.

## 10. Success Metrics (KPIs)
- Quiz completion count per week/month.
- Successful load/save operation rate.
- Reduction in user-reported flow errors over time.
- Mean time to complete key workflows (Create/Update/Quiz/Results).

## 11. Acceptance Criteria
- AC-01: User can complete worksheet management workflows from menu options 1–4.
- AC-02: User can complete ABC CRUD workflows from menu options 5–8.
- AC-03: User can complete all three quiz sections in menu option 9.
- AC-04: Completed quiz attempts appear in menu option 10 with correct timestamp and worksheet name.
- AC-05: The app displays active sheet and worksheet context clearly in menu header.

## 12. Risks and Mitigations
- Risk: API/network interruptions during save/load.
  - Mitigation: Error handling with user-friendly fallback messages.
- Risk: Misconfigured worksheet name.
  - Mitigation: First-worksheet fallback and worksheet management menu.
- Risk: Credential exposure.
  - Mitigation: Keep `.env` and credentials out of source control; restrict access scope.

## 13. Future Enhancements (Optional)
- Per-user progress tracking.
- Exportable quiz analytics summaries.
- Additional spaced-repetition logic.
- Optional web UI front-end.
