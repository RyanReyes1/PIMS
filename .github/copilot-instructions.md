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

**PERMISSION_MATRIX** (`app.py` line ~37): Maps role → list of accessible fields. Add/modify here when changing field access rules.
```python
PERMISSION_MATRIX = {
    'Physician': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Medical Personnel': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Office Staff': ['identity', 'insurance', 'billing'],
    'Volunteer': ['name', 'location', 'approved_visitors', 'restricted_visitation']
}
```

**patients_db** (`app.py` line ~16): In-memory dict. Key: `patient_id` (int), Value: patient dict with fields matching `PERMISSION_MATRIX` keys.

**session['user_role']**: Current user role (no authentication). Defaults to 'Office Staff' on first load (line ~50). Only changes after `/logout` is called.

**session['emergency_access_ids']**: List of patient IDs where current user has elevated physician-level access (used by `/grant_emergency_access`).

## Key Code Patterns

### HTMX Integration Patterns

Routes return **HTML fragments, not JSON**. HTMX swaps fragments into the DOM:

- **Form submission** (`hx-post`): `/submit_patient_search` processes form data, returns filtered `_search_results.html`
- **Out-of-band swaps** (`hx-swap-oob`): `/register_patient` returns simultaneous updates:
  - `hx-swap-oob="beforeend:#patient-tab-headers"` - inserts new tab header
  - `hx-swap-oob="beforeend:#patient-tab-content-area"` - inserts new tab content
  - Response includes inline `<script>` to show new tab and hide others
- **Tab activation**: `/open_patient_tab/<patient_id>` renders role-appropriate template; `base.html` scroll listener auto-scrolls new tabs into view

### RBAC Enforcement Pattern (Two-Layer)

**Backend** (`/edit_patient_section`, `/update_patient_section`, `/download_patient_pdf`, `/export_patient_csv`):
1. Get role: `current_role = session.get('user_role', 'Physician')`
2. Check permission: `if field_name not in PERMISSION_MATRIX.get(current_role, []): return "Access denied"`
3. Return HTML with only permitted fields

**Frontend**:
- Role-specific templates in `templates/components/Patient Information View/Role Defined Templates/`
  - `_patient_tab_physician.html` - all fields
  - `_patient_tab_medicalpersonnel.html` - clinical + admin
  - `_patient_tab_officeworker.html` - billing/identity only
  - `_patient_tab_volunteer.html` - name/location/visitors
- Each includes `_patient_data_section.html` component with field-specific labels and edit triggers

### Component Structure & Naming Conventions

Files use `_` prefix (Jinja2 component convention). Organized by feature:
```
templates/components/
├── Patient Information Management/
│   ├── Patient Search/
│   │   ├── _patient_search.html (search form)
│   │   └── _search_results.html (results list - includes _new_patient_tab_header)
│   ├── _patient_register.html (registration form, submits to /register_patient)
│   └── _emergency_access.html (emergency access form, submits to /grant_emergency_access)
└── Patient Information View/
    ├── _patient_data_section.html (read/edit toggle for single field)
    ├── _edit_field.html (inline edit form)
    ├── _new_patient_tab_header.html (tab button template)
    └── Role Defined Templates/
        ├── _patient_tab_physician.html (all fields)
        ├── _patient_tab_medicalpersonnel.html (medical + admin fields)
        ├── _patient_tab_officeworker.html (billing/identity)
        └── _patient_tab_volunteer.html (name/location/visitors)
```

Each component header (HTML comment) documents parent/children, HTMX behavior, role filtering, and limitations.

### Emergency Access Feature

Routes: `/request_emergency_access_form/<patient_id>` → `/grant_emergency_access/<patient_id>`

- Adds `patient_id` to `session['emergency_access_ids']`
- Logged to console via `log_emergency_access()` for audit trail
- Grants physician-level template access regardless of actual role
- Requires reason submission (form data in `/grant_emergency_access`)
- Session-persisted (lost on logout)

### Adding Patient Fields (Workflow)

1. **Backend** (`app.py`): Add to dummy record (line ~18) and `PERMISSION_MATRIX` with role access
2. **Templates**: Add field to all four `_patient_tab_*.html` files using `_patient_data_section.html` component
3. **Field editing**: Routes handle edits generically; for booleans, detect via `'field' in request.form` pattern

## Tailwind CSS Setup

- **Source**: `static/css/input.css` (edit here; where custom directives go)
- **Output**: `static/css/style.css` (auto-compiled; **never edit directly**)
- **Watcher**: `run.ps1` starts `npx tailwindcss --watch` in background
- **Config**: `tailwind.config.js` scans `templates/**/*.html` and `static/**/*.js` for class names

## Known Limitations & TODOs

- **No authentication**: Session role is hardcoded; production needs proper auth layer
- **In-memory storage**: Patient data + `patient_id_counter` lost on restart; requires DB migration
- **PDF/CSV filenames**: Format is `{firstname}{lastname}_{ext}.{ext}` (lowercase, spaces removed)
- **Filter dropdown**: Close-on-click in `base.html` incomplete; currently unused in UI
- **Deprecated routes**: `/filter_options`, `/print_pdf` (replaced by `/download_patient_pdf`)

## Testing RBAC

To test different roles:
1. Run `.\run.ps1` (starts Flask on http://localhost:5000)
2. Open browser DevTools console and run: `fetch('/logout').then(() => location.reload())`
3. Page reloads with default role (Office Staff)
4. Edit `app.py` line ~50 to set different `session['user_role'] = 'Physician'` (or other role)
5. Restart Flask and reload browser
6. Verify visible fields match `PERMISSION_MATRIX` for that role
7. Test field edits on restricted fields (returns "Access denied" message)