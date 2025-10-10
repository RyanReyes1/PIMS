from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# In a real application, you would use a proper database and ORM
# For demonstration, we'll use a simple in-memory dictionary for patients
patients_db = {}
patient_id_counter = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/logout')
def logout():
    # In a real app, this would clear session, etc.
    return redirect(url_for('index'))

# HTMX Endpoints for Sidebar Actions

@app.route('/request_patient_records', methods=['GET'])
def request_patient_records():
    """Returns the patient search interface."""
    return render_template('components/_patient_search.html')

@app.route('/filter_options', methods=['GET'])
def filter_options():
    """Returns the filter options dropdown."""
    # In a real app, filters might come from a DB
    return render_template('components/_filter_options.html')

@app.route('/search_patients', methods=['GET'])
def search_patients():
    """Handles patient search based on criteria."""
    global patients_db
    search_term = request.args.get('name', '').lower()
    location = request.args.get('location', '').lower()
    restricted_visitation = request.args.get('restricted_visitation') == 'on'
    full_chart = request.args.get('full_chart') == 'on'

    results = [
        patient for patient_id, patient in patients_db.items()
        if search_term in patient['name'].lower() and \
           (not location or location in patient['location'].lower()) and \
           (not restricted_visitation or patient.get('restricted_visitation', False) == restricted_visitation) and \
           (not full_chart or patient.get('full_chart', False) == full_chart)
    ]
    return render_template('components/_search_results.html', patients=results)


@app.route('/register_new_patient', methods=['GET'])
def register_new_patient_form():
    """Returns the patient registration form."""
    return render_template('components/_patient_register.html')

@app.route('/register_patient', methods=['POST'])
def register_patient():
    """Handles new patient registration."""
    global patient_id_counter
    global patients_db
    patient_id_counter += 1
    new_patient = {
        'id': patient_id_counter,
        'name': request.form['name'],
        'location': request.form['location'],
        'approved_visitors': request.form['approved_visitors'],
        'identity': request.form['identity'],
        'insurance': request.form['insurance'],
        'billing': request.form['billing'],
        'restricted_visitation': 'restricted_visitation' in request.form,
        'full_chart': False # Default for new patients
    }
    patients_db[new_patient['id']] = new_patient
    # After registration, you might want to open a tab for the new patient
    # For now, let's just clear the form or show a success message
    return "<div class='p-4 text-green-700 bg-green-100 rounded'>Patient registered successfully!</div>"


@app.route('/request_emergency_access', methods=['GET'])
def request_emergency_access_form():
    """Returns the emergency access form."""
    return render_template('components/_emergency_access.html')

@app.route('/submit_emergency_access', methods=['POST'])
def submit_emergency_access():
    """Handles emergency access submission."""
    reason = request.form['reason']
    # In a real app, this would trigger an alert or a workflow
    return f"<div class='p-4 text-orange-700 bg-orange-100 rounded'>Emergency access request submitted for reason: {reason}</div>"


# HTMX Endpoints for Patient Tabs

@app.route('/open_patient_tab/<int:patient_id>', methods=['GET'])
def open_patient_tab(patient_id):
    """Opens a new tab for a patient."""
    patient = patients_db.get(patient_id)
    if patient:
        return render_template('components/_patient_tab.html', patient=patient)
    return "<div class='text-red-500 p-4'>Patient not found.</div>"

@app.route('/edit_patient_section/<int:patient_id>/<string:field_name>', methods=['GET'])
def edit_patient_section(patient_id, field_name):
    """Renders an editable input for a specific patient field."""
    patient = patients_db.get(patient_id)
    if patient and field_name in patient:
        current_value = patient[field_name]
        return render_template('components/_edit_field.html', patient_id=patient_id, field_name=field_name, current_value=current_value)
    return "<div class='text-red-500 p-4'>Error: Field or patient not found.</div>"


@app.route('/update_patient_section/<int:patient_id>/<string:field_name>', methods=['POST'])
def update_patient_section(patient_id, field_name):
    """Updates a patient field and re-renders the static display."""
    patient = patients_db.get(patient_id)
    if patient and field_name in patient:
        new_value = request.form[f'edit-{field_name}']
        # Handle boolean fields
        if field_name in ['restricted_visitation', 'full_chart']:
            patient[field_name] = (new_value == 'on')
        else:
            patient[field_name] = new_value

        return render_template('components/_patient_data_section.html',
                               patient_id=patient_id,
                               field_name=field_name,
                               label=field_name.replace('_', ' ').title(),
                               value=patient[field_name])
    return "<div class='text-red-500 p-4'>Error: Update failed.</div>"

# Add routes for print PDF and export CSV (placeholder for now)
@app.route('/print_pdf/<int:patient_id>')
def print_pdf(patient_id):
    # In a real app, generate and return a PDF
    return f"<div class='p-4 text-indigo-700 bg-indigo-100 rounded'>Generating PDF for Patient ID: {patient_id}...</div>"

@app.route('/export_csv/<int:patient_id>')
def export_csv(patient_id):
    # In a real app, generate and return a CSV
    return f"<div class='p-4 text-indigo-700 bg-indigo-100 rounded'>Exporting CSV for Patient ID: {patient_id}...</div>"

# ... (existing imports and code) ...

@app.route('/clear_dynamic_content', methods=['GET'])
def clear_dynamic_content():
    """Returns an empty div to clear the dynamic content area."""
    return "<div class='p-4 text-gray-500 bg-gray-50 rounded'>Content cleared. Use the sidebar to continue.</div>"

# ... (rest of your app.py) ...

if __name__ == '__main__':
    app.run(debug=True)