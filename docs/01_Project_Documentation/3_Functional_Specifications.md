# Functional Specifications — Project D

**Document Version:** 1.0  
**Date:** February 24, 2026  
**Status:** Active  

---

## 1. Introduction

This document details the functional requirements, user workflows, and feature specifications for Project D. It describes *what* the system must do, organized by major feature area.

---

## 2. System Overview

Project D is a Streamlit-based web application that manages learning workflows:
- **Worksheet Management**: CRUD operations for organizing knowledge sets
- **Knowledge Pairs**: Manage A–Z key/value pairs with optional Google Maps population
- **Quiz Workflows**: 3-stage learning flow (Practice, Quiz, Final) with adaptive difficulty
- **Results Tracking**: Log and visualize historical quiz performance

---

## 3. User Workflows

### 3.1 Initial Setup

**Actor:** End User  
**Goal:** Create first knowledge set (worksheet)

**Steps:**
1. User launches application
2. System detects no worksheet selected
3. System displays worksheet selection/creation UI
4. User selects or creates worksheet
5. User proceeds to knowledge management or quiz workflows

**Requirements:**
- FR-02: System shall support selecting the first worksheet when none configured
- FR-03: System shall list all worksheets in the active spreadsheet
- FR-04: System shall allow selecting a worksheet by name

---

### 3.2 Knowledge Set Management

#### 3.2.1 Workflow: Create Knowledge Set

**Actor:** Content Creator / Domain Expert  
**Goal:** Create new knowledge set with A–Z pairs

**Preconditions:** Worksheet selected  
**Steps:**
1. User navigates to ABC tab
2. User selects "Create" sub-tab
3. User enters key (A–Z)
4. User enters value(s)
5. Optionally: User selects Google Maps integration to populate values
6. User submits; system saves to Google Sheets
7. System confirms creation

**Functional Requirements:**
- FR-07: System shall create A–Z keys and populate values in target worksheet
- FR-01: System shall connect to Google Sheets using service account credentials
- System shall support multiple values per single key
- System shall validate key format (single A–Z letter)
- System shall provide Google Maps integration for value auto-population

**Data Model:**
```
Knowledge Pair:
  - Key: String (A–Z, required)
  - Values: List[String] (1+ required)
  - Created: Timestamp
  - Modified: Timestamp
```

---

#### 3.2.2 Workflow: Read/View Knowledge Set

**Actor:** End User / Content Creator  
**Goal:** View all A–Z pairs in current worksheet

**Steps:**
1. User navigates to ABC tab → "Read" sub-tab
2. System retrieves all keys and values from Google Sheets
3. System displays formatted table (Key → [Values])
4. User scrolls or filters to review

**Functional Requirements:**
- FR-08: System shall display current A–Z values in read mode
- System shall handle multiple values per key
- System shall sort or display keys alphabetically
- System shall indicate missing keys (gaps in A–Z sequence, optional)

---

#### 3.2.3 Workflow: Update Knowledge Set

**Actor:** Content Creator  
**Goal:** Edit existing A–Z pair values

**Steps:**
1. User navigates to ABC tab → "Update" sub-tab
2. System displays list of existing keys
3. User selects key to modify
4. User updates value(s)
5. User submits; system saves to Google Sheets
6. System confirms update

**Functional Requirements:**
- FR-09: System shall update existing key/value pairs with persistence

---

#### 3.2.4 Workflow: Clear/Reset Values

**Actor:** Content Creator  
**Goal:** Reset all values for a key while preserving the key

**Steps:**
1. User navigates to ABC tab → "Update" sub-tab (or dedicated Clear option)
2. User selects key
3. User confirms clear action
4. System removes all values, preserves key
5. System saves to Google Sheets

**Functional Requirements:**
- FR-10: System shall clear values while preserving keys

---

#### 3.2.5 Workflow: Delete Knowledge Pair

**Actor:** Content Creator  
**Goal:** Remove A–Z pair entirely

**Steps:**
1. User navigates to ABC tab → "Delete" sub-tab
2. User selects key to delete
3. User confirms deletion
4. System removes key and all associated values from Google Sheets
5. System confirms deletion

**Functional Requirements:**
- System shall allow deleting individual/bulk A–Z pairs

---

#### 3.2.6 Worksheet Management

**Actor:** Content Creator / Administrator  
**Goal:** Manage multiple worksheets/knowledge sets

**Workflows:**
- **List Worksheets**: FR-03
- **Select Worksheet**: FR-04
- **Rename Worksheet**: FR-06
- **Delete Worksheet**: FR-05

---

## 4. Quiz Workflows

### 4.1 Quiz Overview

The quiz system implements a 3-stage learning flow based on spaced practice, active recall, and distributed practice:

1. **Practice Stage**: Passive review (encoding)
2. **Quiz Stage**: Randomized active recall with adaptive difficulty
3. **Final Stage**: Alphabetical review (retrieval strength)

---

### 4.2 Practice Stage Workflow

**Actor:** Learner  
**Goal:** Review knowledge pairs passively to establish encoding

**Steps:**
1. User navigates to Quiz tab
2. User selects "Practice" stage
3. System displays 4 knowledge pairs at a time (key + all values)
4. User reviews pairs
5. User navigates forward/backward through sets
6. User completes review (no grading)
7. System records completion timestamp

**Functional Requirements:**
- FR-11: System shall provide a practice stage for review
- System shall display 4 pairs per screen
- System shall allow sequential navigation (previous/next)
- System shall not enforce correctness checks in practice mode
- System shall record completion with timestamp

**User Experience:**
- No time pressure
- All values visible at once
- Clear "Next" and "Previous" buttons
- Progress indicator (e.g., "Set 4 of 8")

---

### 4.3 Quiz Stage Workflow

**Actor:** Learner  
**Goal:** Actively recall knowledge (answer quiz questions) with adaptive difficulty

**Steps:**
1. User navigates to Quiz tab → "Quiz" stage
2. System selects random key from remaining keys
3. System displays: "What is [KEY]?"
4. User enters answer
5. System checks correctness:
   - **Correct**: Acknowledge, mark key as completed (all values submitted), progress to next key
   - **Incorrect**: Provide feedback, increment wrong-answer counter
     - After 3 consecutive wrong answers: Trigger review timer (45 seconds)
     - Increase difficulty: double the required correct attempts for this key (capped at worst case)
6. System repeats until all keys completed or user exits

**Functional Requirements:**
- FR-12: System shall provide randomized quiz stage with correctness checks
- FR-04-A: System shall accept any correct value for a key (multi-value support)
- FR-14: System shall display quiz completion feedback and result persistence
- System shall track submitted values per key (prevent duplicate submissions)
- System shall implement adaptive difficulty (increase required attempts after wrong answers)
- System shall implement 45-second review timer after 3 consecutive wrong answers
- System shall disable quiz input while timer active
- System shall display countdown timer visually

**Adaptive Difficulty Algorithm:**
```
For each key:
  required_correct_attempts = 1 (default)
  
  On incorrect answer:
    consecutive_wrong_count++
    
    if consecutive_wrong_count >= 3:
      trigger_review_timer(45 seconds)
      required_correct_attempts *= 2 (cap at 2+)
    
  On correct answer:
    if submission_count < required_correct_attempts:
      consecutive_wrong_count = 0
      show "correct but need X more"
    else:
      mark_key_completed()
      consecutive_wrong_count = 0
```

**Feedback Display:**
- **Correct (more needed)**: "Correct! You've submitted N of M required values. Keep going!"
- **Correct (final)**: "Excellent! Key moved to completed."
- **Incorrect**: "Not quite. Try again."
- **Already submitted**: "You've already submitted this value for this key."
- **Review Timer Active**: "Please review before continuing. Timer: 45 sec"

**User Experience:**
- Real-time feedback below form
- Progress indicator (e.g., "Key 7 of 26, 19 remaining")
- List of remaining values for current key as Hints
- Clear Submit button
- Session state preserved across page reloads/refreshes

---

### 4.4 Final Stage Workflow

**Actor:** Learner  
**Goal:** Review knowledge in alphabetical order to strengthen retrieval (distributed practice)

**Steps:**
1. User selects "Final" stage from Quiz tab
2. System displays keys in alphabetical order (A → Z)
3. System displays current key, hidden values
4. User enters answer
5. System checks correctness:
   - **All values correct**: Mark key completed, advance to next key
   - **Any incorrect**: Show error, restart (return to A)
6. Repeat until all keys completed

**Functional Requirements:**
- FR-13: System shall provide final alphabetical review stage
- System shall enforce alphabetical order (non-random)
- System shall require all values correct before advancing
- System shall restart on any failure

**User Experience:**
- Alphabetical progress indicator (e.g., "E of Z")
- Error message with restart prompt on failure
- Success message upon completion

---

## 5. Results & Analytics Workflows

### 5.1 Quiz Completion

**Steps:**
1. User completes all 3 stages (Practice → Quiz → Final)
2. System logs completion to dedicated "Quiz Results" worksheet in Google Sheets
3. System displays summary (timestamp, worksheet name, status)

**Functional Requirements:**
- FR-15: System shall store each quiz completion with timestamp, worksheet name, status
- System shall format timestamp as YYYY-MM-DD HH:MM:SS

**Data Model:**
```
Quiz Completion:
  - Timestamp: YYYY-MM-DD HH:MM:SS
  - Worksheet Name: String
  - Status: "Completed" | "In Progress" (optional)
```

---

### 5.2 Results & History View

**Actor:** Learner / Administrator  
**Goal:** View historical quiz performance

**Steps:**
1. User navigates to "Quiz Results" tab
2. System retrieves completion records from Google Sheets
3. System displays table: Timestamp | Worksheet Name | Status
4. User optionally filters/sorts by worksheet or date

**Functional Requirements:**
- FR-16: System shall display historical quiz results in dedicated results view
- System shall sort by timestamp (most recent first, optional)
- System shall allow filtering by worksheet name (optional)

---

## 6. Data Models & Structures

### 6.1 ABC Worksheet Data

```
Key: Single A–Z letter
Values: List[String] — user-generated or imported from Google Maps
Example:
  Key: "A"
  Values: ["Apple", "Apricot", "Avocado"]
```

### 6.2 Quiz Session State

```
session_state:
  quiz_items: List[Tuple(key, [values])]
  quiz_remaining: List[Tuple(key, [values])]
  quiz_required: Dict[key] → int (required correct attempts per key)
  quiz_submitted_values: Dict[key] → [submitted values]
  quiz_streaks: Dict[key] → int (consecutive correct)
  quiz_review_timer: float (epoch timestamp to expire at)
  quiz_feedback: Dict {
    type: "success" | "error" | "warning" | "info"
    message: str
    warning: str (optional)
  }
```

### 6.3 Quiz Results Worksheet

```
Columns: Timestamp, Worksheet Name, Status
Rows (example):
  2026-02-24 14:30:15, "Spanish Vocab", "Completed"
  2026-02-24 15:45:22, "Biology Terms", "Completed"
```

---

## 7. Integration Points

### 7.1 Google Sheets API Integration

**Purpose:** All data persistence (ABC pairs, quiz results)  
**Frequency:** CRUD operations triggered by user actions  
**Error Handling:** User-friendly messages on API failures  
**Caching:** Session-level caching of worksheet data (refresh on demand)  

### 7.2 Google Maps Scraping (Selenium)

**Purpose:** Populate values for knowledge sets (optional)  
**Trigger:** User selects "Google Maps" option in Create workflow  
**Input:** Search query (key name)  
**Output:** List[str] of validated place names  
**Error Handling:** Graceful failure with manual entry fallback  

---

## 8. Non-Functional Requirements

| Requirement | Specification |
|-------------|---------------|
| **Performance** | Common operations complete within <2 sec (quiz submission, CRUD) |
| **Reliability** | ≥99% successful Google Sheets operation rate |
| **Usability** | Readable UI, consistent formatting, clear feedback |
| **Security** | Credentials remain outside source control; service account auth only |
| **Accessibility** | Basic WCAG AA compliance (keyboard navigation, color contrast) |
| **Browser Support** | Chrome, Firefox, Safari (latest 2 versions) |
| **Responsive** | Web-responsive design (mobile-friendly layout) |

---

## 9. Acceptance Criteria

- **AC-01:** User can create a new knowledge set and optionally populate from Google Maps
- **AC-02:** User can read, update, delete knowledge pairs with persistence
- **AC-03:** User can complete all 3 learning stages and receive immediate feedback
- **AC-04:** Quiz difficulty adapts: wrong answers trigger review timers and increased attempts
- **AC-05:** Quiz completions are logged with timestamp, worksheet name, status
- **AC-06:** User can view historical quiz results
- **AC-07:** App displays current knowledge set and progress context throughout UX

---

## 10. Out of Scope (Explicitly Excluded)

- Multi-user concurrent sessions
- Native mobile application
- Advanced BI/analytics dashboards
- Spaced repetition scheduling (interval-based)
- Gamification features (leaderboards, badges)
- AI-powered content recommendations

---

**Document Owner:** Product Owner / Senior Developer  
**Last Updated:** February 24, 2026  
**Next Review Date:** [After architecture review and before development sprint]
