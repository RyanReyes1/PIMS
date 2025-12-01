from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from markupsafe import Markup #if using an older version of Flask, use above line for Markup
from config import Config
from fpdf import FPDF
import csv
import io
import os

app = Flask(__name__)
app.config.from_object(Config)

# In a real application, you would use a proper database and ORM
# For demonstration, we'll use a simple in-memory dictionary for patients
patients_db = {}
patient_id_counter = 0

# Initial dummy data for demonstration
patients_db[1] = {
    'id': 1,
    'name': 'Alice Smith',
    'location': 'Ward A, Room 101',
    'approved_visitors': 'John Smith, Jane Doe',
    'identity': 'AB123456C',
    'insurance': 'BlueCross BlueShield',
    'billing': 'Current',
    'restricted_visitation': False
}
patient_id_counter = 1

# --- RBAC Configuration ---
ROLES = ['Physician', 'Medical Personnel', 'Office Staff', 'Volunteer']

# Permission Matrix: Maps role to a list of fields they can see
PERMISSION_MATRIX = {
    'Physician': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Medical Personnel': ['name', 'location', 'approved_visitors', 'identity', 'insurance', 'billing', 'restricted_visitation'],
    'Office Staff': ['identity', 'insurance', 'billing'],
    'Volunteer': ['name', 'location', 'approved_visitors', 'restricted_visitation']
}
# --- End RBAC Configuration ---


@app.route('/')
def index():
    if 'user_role' not in session:
        session['user_role'] = 'Office Staff' # Set default role on first load
    return render_template('index.html', roles=ROLES, current_role=session['user_role'])

@app.route('/logout')
def logout():
    session.pop('user_role', None) # Clear role on logout
    return redirect(url_for('index'))

@app.route('/clear_dynamic_content', methods=['GET'])
def clear_dynamic_content():
    """Returns an empty div to clear the dynamic content area."""
    return "<div class='p-4 text-gray-500 bg-gray-50 rounded'>Content cleared. Use the sidebar to continue.</div>"

# HTMX Endpoints for Sidebar Actions

@app.route('/request_patient_records', methods=['GET'])
def request_patient_records():
    """Returns the patient search interface."""
    return render_template('components/Patient Information Management/Patient Search/_patient_search.html')

@app.route('/filter_options', methods=['GET'])
def filter_options():
    """Returns the filter options dropdown."""
    # In a real app, filters might come from a DB
    return render_template('components/Patient Information Management/Patient Search/_filter_options.html')

@app.route('/search_patients', methods=['GET'])
def search_patients():
    """Handles patient search based on criteria."""
    global patients_db
    search_term = request.args.get('name', '').lower()
    location = request.args.get('location', '').lower()
    restricted_visitation = request.args.get('restricted_visitation') == 'on'

    results = [
        patient for patient_id, patient in patients_db.items()
        if search_term in patient['name'].lower() and \
           (not location or location in patient['location'].lower()) and \
           (not restricted_visitation or patient.get('restricted_visitation', False) == restricted_visitation)
    ]
    return render_template('components/Patient Information Management/Patient Search/_search_results.html', patients=results)

@app.route('/submit_patient_search', methods=['POST'])
def submit_patient_search():
    """Handles patient search submission via HTMX form submission.
    
    Implements case-insensitive, partial-name search with trailing wildcard logic.
    Searches only the 'name' field of patient records.
    
    Form Data:
    - name: The patient name search term
    
    Returns: Rendered template component with matching patient results
    """
    global patients_db
    
    # Extract search term from form data
    search_term = request.form.get('name', '').strip().lower()
    
    # Perform trailing wildcard search: check if patient name STARTS WITH search term
    # Case-insensitive comparison
    matching_patients = []
    if search_term:  # Only search if term is not empty
        for patient_id, patient in patients_db.items():
            patient_name = patient.get('name', '').lower()
            # Trailing wildcard: name must start with the search term
            if patient_name.startswith(search_term):
                matching_patients.append(patient)
    
    # Render and return the search results component with matching patients
    return render_template(
        'components/Patient Information Management/Patient Search/_search_results.html',
        patients=matching_patients,
        search_term=search_term
    )


@app.route('/register_new_patient', methods=['GET'])
def register_new_patient_form():
    """Returns the patient registration form."""
    return render_template('components/Patient Information Management/_patient_register.html')

@app.route('/register_patient', methods=['POST'])
def register_patient():
    """Handles new patient registration and opens a new patient tab via OOB swap."""
    global patient_id_counter
    global patients_db
    patient_id_counter += 1
    new_patient_id = patient_id_counter

    new_patient = {
        'id': new_patient_id,
        'name': request.form['name'],
        'location': request.form['location'],
        'approved_visitors': request.form['approved_visitors'],
        'identity': request.form['identity'],
        'insurance': request.form['insurance'],
        'billing': request.form['billing'],
        'restricted_visitation': 'restricted_visitation' in request.form
    }
    patients_db[new_patient_id] = new_patient

    # Get current role and determine the correct template
    current_role = session.get('user_role', 'Physician')
    # Map role names to template file names
    role_to_template = {
        'Physician': 'physician',
        'Medical Personnel': 'medicalpersonnel',
        'Office Staff': 'officeworker',
        'Volunteer': 'volunteer'
    }
    template_role = role_to_template.get(current_role, 'physician').lower()
    template_name = f'components/Patient Information View/Role Defined Templates/_patient_tab_{template_role}.html'

    # Generate the HTML for the new patient tab header (OOB swap)
    tab_header_html = render_template('components/Patient Information View/_new_patient_tab_header.html', patient=new_patient)

    # Generate the HTML for the new patient tab content using role-specific template
    tab_content_html = render_template(template_name, patient=new_patient)

    response_html = Markup(f"""
        <div class='p-4 text-green-700 bg-green-100 rounded'>Patient '{new_patient['name']}' registered successfully!</div>

        <div hx-swap-oob="beforeend:#patient-tab-headers" id="oob-header-{new_patient_id}">
            {tab_header_html}
        </div>
        <div hx-swap-oob="beforeend:#patient-tab-content-area" id="oob-content-{new_patient_id}">
            {tab_content_html}
        </div>
        <script>
            htmx.onLoad(function() {{
                const newTabHeader = document.getElementById('tab-header-{new_patient_id}');
                const newTabContent = document.getElementById('patient-tab-{new_patient_id}');
                if (newTabHeader && newTabContent) {{
                    document.querySelectorAll('#patient-tab-content-area > div').forEach(div => div.classList.add('hidden'));
                    document.querySelectorAll('#patient-tab-headers > button').forEach(btn => {{
                        btn.classList.remove('bg-white', 'border-b-0', 'text-gray-900', 'hover:bg-gray-100');
                        btn.classList.add('bg-gray-200', 'text-gray-700', 'hover:bg-gray-300');
                    }});

                    newTabContent.classList.remove('hidden');
                    newTabHeader.classList.add('bg-white', 'border-b-0', 'text-gray-900', 'hover:bg-gray-100');
                    newTabHeader.classList.remove('bg-gray-200', 'text-gray-700', 'hover:bg-gray-300');

                    newTabHeader.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                }}
            }});
        </script>
    """)
    return response_html


@app.route('/request_emergency_access', methods=['GET'])
def request_emergency_access_form():
    """Returns the emergency access form."""
    return render_template('components/Patient Information Management/_emergency_access.html')

@app.route('/submit_emergency_access', methods=['POST'])
def submit_emergency_access():
    """Handles emergency access submission."""
    reason = request.form['reason']
    return f"<div class='p-4 text-orange-700 bg-orange-100 rounded'>Emergency access request submitted for reason: {reason}</div>"


# HTMX Endpoints for Patient Tabs

@app.route('/open_patient_tab/<int:patient_id>', methods=['GET'])
def open_patient_tab(patient_id):
    """Opens a new tab for a patient based on the user's role."""
    patient = patients_db.get(patient_id)
    if not patient:
        return "<div class='text-red-500 p-4'>Patient not found.</div>"

    current_role = session.get('user_role', 'Physician')
    # Map role names to template file names
    role_to_template = {
        'Physician': 'physician',
        'Medical Personnel': 'medicalpersonnel',
        'Office Staff': 'officeworker',
        'Volunteer': 'volunteer'
    }
    template_role = role_to_template.get(current_role, 'physician').lower()
    template_name = f'components/Patient Information View/Role Defined Templates/_patient_tab_{template_role}.html'
    return render_template(template_name, patient=patient)

@app.route('/edit_patient_section/<int:patient_id>/<string:field_name>', methods=['GET'])
def edit_patient_section(patient_id, field_name):
    """Renders an editable input for a specific patient field."""
    current_role = session.get('user_role', 'Physician')
    if field_name not in PERMISSION_MATRIX.get(current_role, []):
        return "<div class='text-red-500 p-4'>Access denied to edit this field.</div>"

    patient = patients_db.get(patient_id)
    if patient and field_name in patient:
        current_value = patient[field_name]
        return render_template('components/Patient Information View/_edit_field.html', patient_id=patient_id, field_name=field_name, current_value=current_value)
    return "<div class='text-red-500 p-4'>Error: Field or patient not found.</div>"


@app.route('/update_patient_section/<int:patient_id>/<string:field_name>', methods=['POST'])
def update_patient_section(patient_id, field_name):
    """Updates a patient field and re-renders the static display."""
    current_role = session.get('user_role', 'Physician')
    if field_name not in PERMISSION_MATRIX.get(current_role, []):
        return "<div class='text-red-500 p-4'>Access denied to update this field.</div>"

    patient = patients_db.get(patient_id)
    if patient and field_name in patient:
        new_value = request.form[f'edit-{field_name}']
        if field_name in ['restricted_visitation']:
            patient[field_name] = (new_value == 'on')
        else:
            patient[field_name] = new_value

        return render_template('components/Patient Information View/_patient_data_section.html',
                               patient_id=patient_id,
                               field_name=field_name,
                               label=field_name.replace('_', ' ').title(),
                               value=patient[field_name])
    return "<div class='text-red-500 p-4'>Error: Update failed.</div>"

@app.route('/create_patient_tab/<int:patient_id>', methods=['GET'])
def create_patient_tab(patient_id):
    """Create patient tab with single-stage role-based filtering.
    
    This endpoint implements role-based RBAC by automatically filtering patient
    data based on the current user's permissions (PERMISSION_MATRIX).
    
    Args:
        patient_id: The ID of the patient to display
    
    Returns:
        HTML fragment (patient tab) with data filtered by user role
    """
    global patients_db
    
    # Verify patient exists
    if patient_id not in patients_db:
        return "<div class='text-red-500 p-4'>Patient not found.</div>"
    
    patient = patients_db[patient_id]
    current_role = session.get('user_role', 'Physician')
    
    # Get role-based permitted fields
    permitted_fields = PERMISSION_MATRIX.get(current_role, [])
    
    # Helper function: Return field value if permitted, else empty string
    def get_field_value(field_name):
        """Returns field value if role is permitted to access it, else empty string."""
        if field_name in permitted_fields:
            return patient.get(field_name, "")
        return ""
    
    # Map role names to patient tab template names
    role_to_template = {
        'Physician': 'physician',
        'Medical Personnel': 'medicalpersonnel',
        'Office Staff': 'officeworker',
        'Volunteer': 'volunteer'
    }
    
    template_role = role_to_template.get(current_role, 'physician').lower()
    template_name = f'components/Patient Information View/Role Defined Templates/_patient_tab_{template_role}.html'
    
    # Render template with filtered data
    return render_template(
        template_name,
        patient=patient,
        get_field_value=get_field_value,
        permitted_fields=permitted_fields
    )

# Add routes for print PDF and export CSV (placeholder for now)
@app.route('/print_pdf/<int:patient_id>')
def print_pdf(patient_id):
    # In a real app, generate and return a PDF
    return f"<div class='p-4 text-indigo-700 bg-indigo-100 rounded'>Generating PDF for Patient ID: {patient_id}...</div>"

@app.route('/download_patient_pdf/<int:patient_id>')
def download_patient_pdf(patient_id):
    """Generate and download a PDF of patient data with RBAC enforcement.
    
    This route generates a PDF file containing only the fields that the current
    user's role is permitted to access based on the PERMISSION_MATRIX.
    
    Args:
        patient_id: The ID of the patient to export
    
    Returns:
        PDF file download with filename format: {firstname}{lastname}_pdf.pdf
    """
    # Verify patient exists
    patient = patients_db.get(patient_id)
    if not patient:
        return "<div class='text-red-500 p-4'>Patient not found.</div>", 404
    
    # Get current user's role and permitted fields
    current_role = session.get('user_role', 'Physician')
    permitted_fields = PERMISSION_MATRIX.get(current_role, [])
    
    # Create filtered patient data dictionary with only permitted fields
    filtered_patient_data = {}
    for field in permitted_fields:
        if field in patient:
            filtered_patient_data[field] = patient.get(field, '')
    
    # Initialize PDF object with explicit margins and configure layout
    pdf = FPDF()
    pdf.set_margins(10, 10, 10)  # Explicitly set margins (left, top, right)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Add patient name as title
    patient_name = patient.get('name', 'Patient Record')
    pdf.cell(0, 10, f"Patient: {patient_name}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Arial", "", 11)
    pdf.ln(5)  # Add some spacing
    
    # Add field data to PDF with explicit positioning and width
    # A4 page width is 210mm, with 10mm margins on each side = 190mm usable width
    usable_width = 190
    line_height = 8
    
    for field_name, field_value in filtered_patient_data.items():
        # Format field name: replace underscores with spaces and title case
        formatted_label = field_name.replace('_', ' ').title()
        
        # Convert boolean values to readable strings
        if isinstance(field_value, bool):
            field_value = "Yes" if field_value else "No"
        
        # Add field to PDF with proper positioning
        # Move to left margin at beginning of each field
        pdf.set_x(10)  # Set X position to left margin
        pdf_text = f"{formatted_label}: {field_value}"
        # Use multi_cell with proper width and move to next line after
        pdf.multi_cell(usable_width, line_height, pdf_text, new_x="LMARGIN", new_y="NEXT")
    
    # Construct filename: extract first and last names, convert to lowercase, remove spaces
    patient_name_parts = patient.get('name', 'patient').split()
    firstname = patient_name_parts[0].lower() if patient_name_parts else 'patient'
    lastname = patient_name_parts[-1].lower() if len(patient_name_parts) > 1 else ''
    
    # Remove spaces from names
    firstname = firstname.replace(' ', '')
    lastname = lastname.replace(' ', '')
    
    # Build filename: {firstname}{lastname}_pdf.pdf
    filename = f"{firstname}{lastname}_pdf.pdf"
    
    # Generate PDF to bytes
    pdf_bytes = io.BytesIO(pdf.output())
    pdf_bytes.seek(0)
    
    return send_file(
        pdf_bytes,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@app.route('/export_patient_csv/<int:patient_id>')
def export_patient_csv(patient_id):
    """Export patient data as CSV with RBAC enforcement.
    
    This route generates a CSV file containing only the fields that the current
    user's role is permitted to access based on the PERMISSION_MATRIX.
    
    Args:
        patient_id: The ID of the patient to export
    
    Returns:
        CSV file download with filename format: {firstname}{lastname}_csv.csv
    """
    # Verify patient exists
    patient = patients_db.get(patient_id)
    if not patient:
        return "<div class='text-red-500 p-4'>Patient not found.</div>", 404
    
    # Get current user's role and permitted fields
    current_role = session.get('user_role', 'Physician')
    permitted_fields = PERMISSION_MATRIX.get(current_role, [])
    
    # Create filtered patient data dictionary with only permitted fields
    filtered_patient_data = {}
    for field in permitted_fields:
        filtered_patient_data[field] = patient.get(field, '')
    
    # Generate CSV in memory using io.StringIO
    csv_buffer = io.StringIO()
    fieldnames = list(filtered_patient_data.keys())
    
    writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerow(filtered_patient_data)
    
    # Prepare CSV content for download
    csv_buffer.seek(0)
    csv_content = csv_buffer.getvalue()
    
    # Construct filename: extract first and last names, convert to lowercase, remove spaces
    patient_name = patient.get('name', 'patient').split()
    firstname = patient_name[0].lower() if patient_name else 'patient'
    lastname = patient_name[-1].lower() if len(patient_name) > 1 else ''
    
    # Remove spaces from names
    firstname = firstname.replace(' ', '')
    lastname = lastname.replace(' ', '')
    
    # Build filename: {firstname}{lastname}_csv.csv
    filename = f"{firstname}{lastname}_csv.csv"
    
    # Convert string content to bytes for send_file
    csv_bytes = io.BytesIO(csv_content.encode('utf-8'))
    csv_bytes.seek(0)
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


# --- RBAC Role Switching Endpoint ---



if __name__ == '__main__':
    app.run(debug=True)