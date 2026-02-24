# Docs Overview

This folder contains Project D's official documentation, generated reports, architecture diagrams, and reference materials.

## 📚 Start Here: Project Documentation

**→ [01_Project_Documentation/](01_Project_Documentation/)** — Core project documentation (start here!)

This folder contains the authoritative project documents in best-practice order:
1. **Project Charter** — Vision, business case, success criteria
2. **Business Requirements** — Objectives, scope, constraints, KPIs
3. **Functional Specifications** — Features, workflows, use cases
4. **Technical Architecture** — Design, tech stack, components, data flow
5. **Implementation Guide** — Setup, installation, deployment

**Quick Navigation:**
- **For managers/stakeholders:** Start with Project Charter → Business Requirements
- **For developers:** Start with Functional Specifications → Technical Architecture → Implementation Guide
- **For architects:** Start with Technical Architecture

---

## 📁 Folder Structure

```
docs/
├── 01_Project_Documentation/    ← Main project documentation (READ THIS FIRST)
│   ├── README.md
│   ├── 1_Project_Charter.md
│   ├── 2_Business_Requirements.md
│   ├── 3_Functional_Specifications.md
│   ├── 4_Technical_Architecture.md
│   └── 5_Implementation_Guide.md
│
├── diagrams/                     ← Architecture and system diagrams
│   ├── *.svg files
│   └── *.dot and .mmd sources
│
├── generated/                    ← Auto-generated reports (reference only)
│   ├── Function_Inventory_Report.md
│   ├── Project_D_Development_Report.txt
│   └── Project_D_Development_Report.html
│
└── templates/                    ← Document templates and examples
    └── Report_Templates_Pack.md
```

---

## 🎯 Key Project Information

**Project:** Project D — Memory & Learning Application  
**Status:** Web-UI-only (legacy CLI removed)  
**Tech Stack:** Streamlit, Python, Google Sheets, Selenium  
**Purpose:** Evidence-based learning platform with adaptive quiz mechanics

---

## 📊 Reference Materials

### Architecture Diagrams
Located in `diagrams/` folder:
- System architecture and component relationships
- Package dependencies
- Call flow diagrams
- High-level workflow diagrams

### Generated Reports
Located in `generated/` folder (auto-generated, for reference):
- **Function_Inventory_Report.md** — Inventory of all utility functions
- **Project_D_Development_Report.txt** — Plain-text development summary
- **Project_D_Development_Report.html** — HTML version of development summary

### Templates
Located in `templates/` folder:
- **Report_Templates_Pack.md** — Templates for creating new reports

---

## 🔧 Development Notes

Project D is now **web-UI-only** following removal of legacy CLI functionality. All code is organized in:
- `web_app.py` — Main Streamlit application
- `app.py` — Utility functions (Google Maps scraping)

For full information on architecture and development, see [4_Technical_Architecture.md](01_Project_Documentation/4_Technical_Architecture.md).

---

**Last Updated:** February 24, 2026  
**Document Curator:** Project Team
