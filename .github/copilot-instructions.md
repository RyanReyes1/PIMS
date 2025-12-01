# PIMS (Patient Information Management System) - AI Agent Instructions

## Quick Start
Run `.\run.ps1` from project root (Windows PowerShell). This script:
1. Creates/activates Python venv and installs Flask dependencies (`requirements.txt`: Flask, fpdf2)
2. Installs Node.js dependencies and starts Tailwind CSS watcher in background
3. Launches Flask dev server (http://localhost:5000)

Use flags: `.\run.ps1 -NoPython` or `.\run.ps1 -NoTailwind` to skip steps. Press Ctrl+C to stop.

## Architecture Overview

**PIMS** is a Flask-based hospital patient management system with field-level role-based access control (RBAC). The design enforces permissions at two layers: backend (Flask routes) and frontend (role-specific Jinja2 templates). Data is stored in-memory (`patients_db` dict in `app.py`; planned DB migration).

### Critical Data Structures

**PERMISSION_MATRIX** (line ~37 in `app.py`): Maps role → list of accessible fields
```python
PERMISSION_MATRIX = {
    'Physician': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Medical Personnel': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Office Staff': ['identity', 'insurance', 'billing'],
    'Volunteer': ['name', 'location', 'approved_visitors', 'restricted_visitation']
}
```

**patient_db** (line ~16): In-memory dictionary. Key: `patient_id` (int), Value: patient dict with fields matching `PERMISSION_MATRIX` keys.

**Session Role** (`session['user_role']`): Tracks current user role; defaults to 'Office Staff' on first load (line ~50).

## Key Code Patterns

### HTMX Integration Patterns

Routes return **HTML fragments, not JSON**. HTMX swaps fragments into the DOM:

- **`hx-post` with form submission**: `/submit_patient_search` processes form data, returns `_search_results.html` fragment
- **Out-of-band swaps** (`hx-swap-oob`): Used in `/register_patient` to insert new tab headers and content simultaneously
  - Headers swap into `#patient-tab-headers` (beforeend)
  - Content swaps into `#patient-tab-content-area` (beforeend)
- **Tab activation JS**: `/register_patient` response includes inline `<script>` that hides other tabs, shows new one, scrolls into view

Example: `_patient_register.html` submits to `/register_patient` which returns OOB swaps + success message + activation script.

### RBAC Enforcement Pattern

**Backend enforcement** (`/edit_patient_section`, `/update_patient_section`, PDF/CSV export):
1. Get role: `current_role = session.get('user_role', 'Physician')`
2. Check permission: `if field_name not in PERMISSION_MATRIX.get(current_role, []): return error`
3. Render template with filtered data

**Frontend enforcement**:
- Role-specific templates in `templates/components/Patient Information View/Role Defined Templates/`
- Examples: `_patient_tab_physician.html` includes all fields; `_patient_tab_officeworker.html` includes only billing/insurance/identity
- Templates use conditional rendering and loop through field lists to match backend permissions

### Component Structure & Naming Conventions

Files use `_` prefix (Jinja2 component convention). Organized by feature:
```
templates/components/
├── Patient Information Management/
│   ├── Patient Search/
│   │   ├── _patient_search.html
│   │   └── _search_results.html
│   ├── _patient_register.html
│   └── _emergency_access.html
└── Patient Information View/
    ├── _patient_data_section.html (editable field display)
    ├── _edit_field.html (inline edit form)
    ├── _new_patient_tab_header.html
    └── Role Defined Templates/
        ├── _patient_tab_physician.html
        ├── _patient_tab_medicalpersonnel.html
        ├── _patient_tab_officeworker.html
        └── _patient_tab_volunteer.html
        └── _patient_tab.html (base template)
```

**Component headers** (HTML comments) document:
- Parent/child relationships
- HTMX behavior
- Role-specific filtering
- Known limitations

### Adding Patient Fields (Workflow)

1. **Backend** (`app.py`): Add field to `patients_db` dummy record (line ~18)
2. **RBAC** (`app.py`): Update `PERMISSION_MATRIX` with role access rules
3. **Templates**: Add field include in all four role-specific templates using `_patient_data_section.html` with proper labels
4. **Field editing**: Routes `/edit_patient_section` and `/update_patient_section` already handle generic field updates; ensure type handling (e.g., booleans converted via `'field' in request.form`)

## Tailwind CSS Setup

- **Source**: `static/css/input.css` (where custom directives go)
- **Output**: `static/css/style.css` (auto-compiled; **do NOT edit directly**)
- **Watcher**: `run.ps1` starts `npx tailwindcss --watch` in background
- **Config**: `tailwind.config.js` scans `templates/**/*.html` and `static/**/*.js` for class names

## Known Limitations & TODOs

- **Session-based roles**: No authentication; testing involves changing `session['user_role']` and logging out
- **In-memory storage**: Patient ID counter (`patient_id_counter`) will need persistence layer when migrating to database
- **PDF/CSV exports**: Implemented with RBAC filtering; filenames use `{firstname}{lastname}_ext` format (lowercase, no spaces)
- **Filter dropdown**: Close-on-click behavior in `base.html` (line ~23) noted as potentially incomplete; currently depreciated in UI
- **Deprecated routes**: `/filter_options`, `/print_pdf` (superseded by `/download_patient_pdf`)

## Testing RBAC

Change role and verify permissions:
1. Run `.\run.ps1`
2. Open DevTools console: `fetch('/logout').then(() => location.reload())`
3. Log in as different role (dropdown in header)
4. Verify visible fields match `PERMISSION_MATRIX`
5. Test field edit attempts on restricted fields (should fail with "Access denied" message)