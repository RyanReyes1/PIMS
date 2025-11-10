# PIMS (Patient Information Management System) - AI Agent Instructions

## Project Overview
PIMS is a Flask-based hospital management system with a focus on patient information management and role-based access control (RBAC). The system uses HTMX for dynamic UI updates and Tailwind CSS for styling.

## Architecture and Components

### Backend (Python/Flask)
- Main application: `app.py` - Contains route handlers and RBAC configuration
- Configuration: `config.py` - App configuration and environment variables
- Current state: Uses in-memory storage (dictionary) for patient data, marked for future database integration

### Frontend
- Template Structure:
  - `templates/base.html` - Base template with common scripts and styles
  - `templates/components/` - Modular UI components
  - HTMX for dynamic content updates without full page reloads
  - Tailwind CSS for styling (`static/css/`)

## Key Patterns and Conventions

### Role-Based Access Control (RBAC)
- Roles defined in `app.py`: Physician, Medical Personnel, Office Staff, Volunteer
- Field-level permissions managed through `PERMISSION_MATRIX`
- Access checks via `can_access_field()` function, available in templates

### Component Structure
- Components are prefixed with underscore (e.g., `_patient_tab.html`)
- Each component file includes documentation header with parent/child relationships
- HTMX attributes used for dynamic loading and updates

### Frontend Interactions
- HTMX event handlers in `base.html` for smooth UI updates
- Component-specific JavaScript kept minimal, preferring HTMX where possible
- Dynamic content managed through dedicated endpoints (e.g., `/clear_dynamic_content`)

## Development Workflow

### Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Run development server: `flask run`

### Making Changes
- Backend changes: Update route handlers in `app.py`
- Frontend components: Add/modify files in `templates/components/`
- Styles: Modify `static/css/input.css` for Tailwind customizations

## Key Integration Points
- HTMX and server endpoints (see routes in `app.py`)
- Role-based permission checks between backend and frontend
- Future database integration points marked in `app.py` and `config.py`

## Common Tasks
- Adding new patient fields: Update `PERMISSION_MATRIX` and relevant templates
- Creating new components: Follow naming convention and document parent/child relationships
- Implementing new features: Consider RBAC implications and update permissions accordingly

## Future Development Notes
- Database integration planned (see comments in `config.py`)
- Enhanced security measures needed for production
- Additional patient management features marked for implementation