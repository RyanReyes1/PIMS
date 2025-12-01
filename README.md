# PIMS - Patient Information Management System

A Flask-based hospital patient management system with field-level role-based access control (RBAC). PIMS enables healthcare staff to securely manage patient records with permissions enforced at both the backend and frontend layers.

## Features

- **Role-Based Access Control (RBAC)**: Four-tier permission system (Physician, Medical Personnel, Office Staff, Volunteer)
- **Field-Level Permissions**: Granular control over which patient data fields each role can access
- **HTMX Integration**: Dynamic, interactive user interface without full page reloads
- **Patient Management**: Search, register, view, and edit patient records
- **Data Export**: Generate PDF and CSV reports with role-based filtering
- **Emergency Access**: Restricted access controls for emergency situations
- **Tailwind CSS**: Modern, responsive styling with utility-first CSS framework

## Handwritten Notes

- There is no dropdown menu to change roles, that was a feature depreciated a while ago because it didn't work. I think the AI got confused when I mentioned the feature. I will try to remove all references to it in this file.

## Quick Start

### Prerequisites

- Python 3.7+
- Node.js 14+
- Windows PowerShell (for startup script) or terminal with bash/sh

### Installation & Running

**Windows PowerShell (Recommended):**
```powershell
.\run.ps1
```

This script will:
1. Create and activate a Python virtual environment
2. Install Flask dependencies from `requirements.txt`
3. Install Node.js dependencies
4. Start the Tailwind CSS watcher in the background
5. Launch the Flask development server at `http://localhost:5000`

**Skip Steps (Optional Flags):**
```powershell
.\run.ps1 -NoPython      # Skip Python setup
.\run.ps1 -NoTailwind    # Skip Tailwind CSS watcher
```

**Stop the Server:**
Press `Ctrl+C` to stop the Flask server. The script will clean up background processes automatically.

### Manual Setup

**Python:**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
flask run
```

**Tailwind CSS (in separate terminal):**
```bash
npm install
npx tailwindcss -i ./static/css/input.css -o ./static/css/style.css --watch
```

Access the application at `http://localhost:5000`

## Project Structure

```
PIMS/
├── app.py                          # Flask application & route handlers
├── config.py                       # Configuration settings
├── requirements.txt                # Python dependencies
├── package.json                    # Node.js dependencies
├── tailwind.config.js              # Tailwind CSS configuration
├── run.ps1                         # Startup script (Windows)
├── static/
│   ├── css/
│   │   ├── input.css              # Tailwind CSS source (edit here)
│   │   └── style.css              # Compiled CSS output (auto-generated)
│   └── js/
│       └── htmx.min.js            # HTMX library
├── templates/
│   ├── base.html                   # Base template with layout
│   ├── index.html                  # Home page
│   ├── layout.html                 # Layout wrapper
│   └── components/
│       ├── Header/                 # Header component
│       ├── Patient Information Management/
│       │   ├── Patient Search/     # Search interface & results
│       │   ├── Patient Register/   # Patient registration form
│       │   └── Emergency Access/   # Emergency access controls
│       └── Patient Information View/
│           ├── Patient Data Display
│           ├── Field Editing
│           └── Role Defined Templates/ # Role-specific views
└── __pycache__/                    # Python cache (auto-generated)
```

## Architecture Overview

### RBAC System

PIMS enforces role-based permissions at two layers:

#### Backend (Flask Routes)
Routes check `session['user_role']` against the `PERMISSION_MATRIX` before returning patient data:
```python
PERMISSION_MATRIX = {
    'Physician': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Medical Personnel': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Office Staff': ['identity', 'insurance', 'billing'],
    'Volunteer': ['name', 'location', 'approved_visitors', 'restricted_visitation']
}
```

#### Frontend (Jinja2 Templates)
Role-specific templates in `templates/components/Patient Information View/Role Defined Templates/` render only permitted fields:
- `_patient_tab_physician.html` - Full access
- `_patient_tab_medicalpersonnel.html` - Clinical & administrative data
- `_patient_tab_officeworker.html` - Billing & identity only
- `_patient_tab_volunteer.html` - Basic visitor & location info

### Data Storage

Currently uses in-memory storage (`patients_db` dict in `app.py`):
```python
patients_db = {
    patient_id: {
        'id': int,
        'name': str,
        'location': str,
        'approved_visitors': str,
        'identity': str,
        'insurance': str,
        'billing': str,
        'restricted_visitation': bool
    }
}
```

**Note:** Ready for migration to persistent database (SQL/NoSQL).

### HTMX Integration

Routes return HTML fragments (not JSON) that HTMX swaps into the DOM:

**Form Submission:**
- `hx-post="/submit_patient_search"` → returns `_search_results.html`

**Out-of-Band Swaps:**
- Multiple DOM regions update simultaneously in a single response
- Used in patient registration to update tab headers and content areas

**Key Components:**
- `/request_patient_records` - Patient search interface
- `/register_patient` - New patient registration with dynamic tab creation
- `/edit_patient_section` - Inline field editing
- `/download_patient_pdf` - PDF generation with RBAC filtering

## Key Concepts

### Testing Different Roles

1. Change the user_role in app.py line 46 to desired role
2. Start the application: `.\run.ps1`
3. Press the **Logout** button to apply role changes
4. Verify that visible fields match the `PERMISSION_MATRIX`

### Adding a New Patient Field

1. **Backend** (`app.py`):
   - Add field to the dummy patient record (line ~18)
   - Update `PERMISSION_MATRIX` with role access rules

2. **Templates**:
   - Add field to all four role-specific templates using `_patient_data_section.html` component
   - Add field to inline edit form (`_edit_field.html`)

3. **Field Editing**:
   - Routes `/edit_patient_section` and `/update_patient_section` handle updates generically
   - Boolean fields are detected via `'field' in request.form` pattern

### Styling with Tailwind CSS

- **Edit**: `static/css/input.css` (add custom directives here)
- **Auto-compile**: `npx tailwindcss --watch` compiles to `static/css/style.css`
- **Don't edit**: Never manually edit `style.css` — it's auto-generated
- **Config**: `tailwind.config.js` scans templates and JS for class names

## Dependencies

### Python
- **Flask** - Web framework
- **fpdf2** - PDF generation

### JavaScript
- **HTMX** - Dynamic HTML framework
- **Tailwind CSS** - Utility-first CSS framework

See `requirements.txt` and `package.json` for versions.

## Known Limitations

- **Session-based roles**: No authentication
- **In-memory storage**: Patient data lost on server restart; database migration needed for production
- **Patient ID counter**: `patient_id_counter` variable requires persistence layer for real-world use
- **Export filenames**: Use lowercase, space-removed format (e.g., `alicesmith_report.pdf`)

## Deprecated Features

- `/filter_options` - Removed from current UI
- `/print_pdf` - Superseded by `/download_patient_pdf`

## Configuration

Edit `config.py` to customize:
- Secret key
- Flask debug mode
- Session settings
- Other application configuration

## Production Considerations

Before deploying to production:

1. **Authentication**: Replace role dropdown with proper user authentication
2. **Database**: Migrate from in-memory `patients_db` to persistent storage
3. **Session Storage**: Use secure session backend (Redis, database)
4. **HTTPS**: Enable HTTPS with proper SSL certificates
5. **CORS**: Configure proper CORS policies
6. **Logging**: Implement comprehensive audit logging for HIPAA compliance
7. **Data Encryption**: Encrypt sensitive patient data at rest and in transit

## Troubleshooting

**Flask server won't start:**
- Ensure port 5000 is not in use
- Check that `requirements.txt` packages are installed
- Verify Python virtual environment is activated

**Tailwind CSS not updating:**
- Ensure the watcher is running (check background jobs: `Get-Job` in PowerShell)
- Edit `static/css/input.css`, not `style.css`
- Restart the watcher if changes don't apply

**Role changes not reflecting:**
- Click **Logout** button after changing the role dropdown
- Check browser DevTools console for errors

## Contributing

When contributing to PIMS:

1. Follow the component structure in `templates/components/`
2. Update both `PERMISSION_MATRIX` and role-specific templates when changing access
3. Prefix component files with `_` (Jinja2 convention)
4. Add component headers documenting HTMX behavior and permissions

## License

[Specify your license here]

## Support

For issues and questions, please contact the development team or open an issue in the repository.

---

**Last Updated**: December 2025
