# PIMS (Patient Information Management System) - AI Agent Instructions

## Quick Start
Run `.\run.ps1` from project root (Windows PowerShell). This script:
1. Creates/activates Python venv and installs Flask dependencies
2. Installs Node.js dependencies and starts Tailwind CSS watcher in background
3. Launches Flask dev server (http://localhost:5000)

Use flags: `.\run.ps1 -NoPython` or `.\run.ps1 -NoTailwind` to skip steps.

## Architecture Overview

**PIMS** is a Flask-based hospital patient management system with field-level role-based access control (RBAC). The design separates concerns into:

- **Backend**: Flask routes in `app.py` handle RBAC logic, patient CRUD, and HTMX endpoints
- **Frontend**: Jinja2 templates using HTMX for dynamic partial updates + Tailwind CSS styling
- **Storage**: In-memory patient dictionary (planned DB migration)

### RBAC Model
The system enforces permissions at two layers:

1. **Backend layer** (`app.py`):
   - `PERMISSION_MATRIX` dict maps role → list of accessible fields
   - Routes like `/open_patient_tab` check permissions before rendering templates
   - Example: Office Staff can only see `identity`, `insurance`, `billing`

2. **Template layer**:
   - Role-specific templates in `templates/components/Patient Information View/Role Defined Templates/`
   - Example: `_patient_tab_physician.html` vs `_patient_tab_volunteer.html` render different field subsets
   - Session stores current role: `session['user_role']`

## Key Code Patterns

### Adding Patient Fields
1. Add field to dummy patient in `app.py` (line ~18)
2. Update `PERMISSION_MATRIX` with role access rules
3. Update role-specific templates (physician, medical personnel, office worker, volunteer)
4. Field edit/update handled by `/edit_patient_section` and `/update_patient_section` routes

### HTMX Integration
Routes return HTML fragments, not JSON. HTMX attributes swap responses into DOM:
- `hx-get="/endpoint"` — fetches and loads content
- `hx-post="/endpoint"` — form submission (e.g., search, patient registration)
- `hx-swap-oob="beforeend:#container"` — out-of-band swap for inserting new patient tabs
- All tabs swap into `#patient-tab-content-area`; headers swap into `#patient-tab-headers`

### Component Structure
Files use `_` prefix and are organized by feature:
```
templates/components/
├── Patient Information Management/
│   ├── Patient Search/
│   │   ├── _patient_search.html
│   │   └── _search_results.html
│   ├── _patient_register.html
│   └── _emergency_access.html
└── Patient Information View/
    └── Role Defined Templates/
        ├── _patient_tab_physician.html
        ├── _patient_tab_medicalpersonnel.html
        ├── _patient_tab_officeworker.html
        └── _patient_tab_volunteer.html
```

Each component header documents parent/child relationships and HTMX behavior.

### Search Workflow
`_patient_search.html` → user submits → `/submit_patient_search` → returns `_search_results.html` with matching patients → user clicks patient → `/open_patient_tab/{id}` renders role-filtered tab.

## Tailwind CSS Setup
- Source: `static/css/input.css` (where custom directives go)
- Output: `static/css/style.css` (auto-compiled, do NOT edit directly)
- Watcher: `run.ps1` starts `npx tailwindcss --watch` in background
- Config: `tailwind.config.js` includes all template paths for class scanning

## Notes
- Session-based user role switching (no auth system currently)
- Patient ID counter managed in memory; will need adjustment when using DB
- Print PDF and export CSV routes are placeholders
- Filter dropdown close behavior in `base.html` noted as potentially incomplete