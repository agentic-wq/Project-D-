# Project D: Project Charter

**Project Name:** Project D — Memory & Learning Application  
**Document Version:** 1.0  
**Date:** February 24, 2026  
**Status:** Active  

---

## 1. Executive Summary

Project D is a web-based memory and learning application that enables users to encode, practice, and retain structured knowledge (A–Z key/value pairs) through evidence-based learning techniques combined with adaptive quiz mechanics. The application leverages spaced practice, active recall, and adaptive difficulty to maximize knowledge retention and learning outcomes.

---

## 2. Project Sponsor & Key Stakeholders

| Role | Name/Description | Responsibilities |
|------|------------------|------------------|
| **Product Owner** | [To be assigned] | Define learning flows, priority features, success criteria |
| **Project Manager** | [To be assigned] | Timeline, resource allocation, risk management |
| **Lead Developer** | [To be assigned] | Architecture decisions, code quality, technical direction |
| **Domain Expert** | [To be assigned] | Content curation, learning methodology validation |
| **End Users** | Learners | Provide feedback on UX, engagement, effectiveness |

---

## 3. Business Drivers & Case

### Problem Statement
Knowledge retention is challenging without structured, active practice. Traditional passive review (reading, flashcards) does not leverage evidence-based learning science principles like spaced practice and adaptive difficulty.

### Solution
A web-based learning platform that:
- Guides users through a 3-stage learning flow (Practice → Quiz → Final)
- Adapts difficulty based on performance (harder questions after wrong answers)
- Provides evidence-based feedback and review timers
- Persists progress via Google Sheets for simple data management

### Value Proposition
- **For Learners**: Faster knowledge retention, better long-term recall, science-backed methodology
- **For Content Creators**: Easy knowledge set creation and management; Google Maps integration for rapid data capture
- **For Organizations**: Scalable learning tool with minimal infrastructure (web + Google Sheets)

---

## 4. Project Vision & Mission

**Vision:** A memory and learning application that empowers learners to achieve mastery through evidence-based cognitive science.

**Mission:** Provide an intuitive, web-based platform for encoding structured knowledge, practicing with adaptive difficulty, and achieving measurable learning outcomes.

---

## 5. High-Level Objectives

1. **Enable Efficient Knowledge Encoding**
   - Users can create and manage A–Z knowledge sets with minimal friction
   - Google Maps integration for rapid data population

2. **Maximize Learning Retention**
   - 3-stage learning flow based on spaced practice and active recall
   - Adaptive difficulty scales based on user performance

3. **Provide Measurable Progress**
   - Timestamped quiz completion records
   - Historical performance tracking and visibility

4. **Ensure User Engagement**
   - Performance-based feedback and encouragement
   - Review timers promote metacognition

5. **Support Scalable Persistence**
   - Google Sheets backend for simple, no-database setup
   - Multi-worksheet support for organizing learning sets

---

## 6. Key Success Criteria (KPIs)

| KPI | Target | Measurement |
|-----|--------|-------------|
| **Learning Engagement** | ≥70% quiz completion rate per active user | Weekly/monthly completion tracking |
| **Knowledge Retention** | ≥80% progression through all 3 stages | Session state analytics |
| **Time-to-Mastery** | <7 days average per knowledge set | Historical timestamp analysis |
| **Platform Reliability** | ≥99% successful load/save operations | Request logging and error tracking |
| **User Experience** | ≥90% error-free quiz flow completion | Session state validation |
| **Setup Friction** | <5 minutes to first quiz | User feedback, timing logs |

---

## 7. Scope (High-Level)

### In Scope
- Web-based learning application (Streamlit frontend)
- Knowledge set (worksheet) management (CRUD)
- A–Z key/value pair persistence (Google Sheets)
- 3-stage learning workflow (Practice, Quiz, Final)
- Quiz completion logging and historical tracking
- Google Maps data scraping for rapid content capture

### Out of Scope
- Native mobile application (responsive web only)
- Advanced BI dashboards (limited to Google Sheets features)
- Multi-user/multi-learner with separate progress (single-user per session)
- Interval-based spaced repetition scheduling
- Gamification (leaderboards, badges, streaks)
- AI-powered content generation

---

## 8. Timeline & Milestones (High-Level)

| Milestone | Target Date | Deliverable |
|-----------|------------|-------------|
| **MVP** | Complete | Web UI with 3-stage quiz, CRUD, Google Sheets integration |
| **Documentation** | 2026-02-24 | Project Charter, Requirements, Specs, Architecture, Implementation Guide |
| **Production Readiness** | [To be determined] | Performance tuning, security audit, deployment procedure |
| **User Testing** | [To be determined] | Feedback collection, retention metrics validation |

---

## 9. Assumptions

- Valid Google service account credentials will be provided and maintained
- Users have basic browser/keyboard interaction capability
- Google Sheets API availability (current SLA ≥99.9%)
- Users operate one active worksheet context per session
- Knowledge content is curated by domain experts (quality not automated)

---

## 10. Risks & Constraints

### Major Risks
| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| Google Sheets API rate limits or outages | High | Low | Implement caching, monitoring, fallback messaging |
| Poor content quality degrades learning outcomes | High | Medium | Domain expert review cycle, user feedback integration |
| Adaptive algorithm miscalibration | Medium | Medium | A/B testing, user feedback surveys, parameter tuning |
| Web scraping Selenium fragility | Medium | Medium | Maintain fallback data sources, update DOM selectors regularly |

### Key Constraints
- Dependent on Google API availability
- Selenium browser automation reliability
- Single-user session model (not multi-user concurrent)
- No offline functionality

---

## 11. Authorization & Approval

| Role | Signature | Date | Notes |
|------|-----------|------|-------|
| **Project Sponsor** | __________ | __________ | Authorizes project initiation and funding |
| **Product Owner** | __________ | __________ | Approves scope, vision, success criteria |
| **Technical Lead** | __________ | __________ | Confirms feasibility and approach |

---

## 12. Document Approvals

- [ ] Project Sponsor approval
- [ ] Product Owner approval
- [ ] Technical Lead approval
- [ ] Design/UX review (if applicable)

---

## Next Steps

1. **Distribute** to stakeholders for review and approval
2. **Schedule kickoff** discussion with team
3. **Proceed to** Business Requirements Document (BRD)
4. **Establish** communication and decision-making channels

---

**Document Owner:** Project Manager  
**Last Updated:** February 24, 2026  
**Next Review Date:** [To be scheduled after approval]
