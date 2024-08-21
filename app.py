from flask import Flask, render_template, request, redirect, url_for, send_file, session
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
import csv
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a strong secret key for session management

# Disable SSL certificate verification (optional, not recommended for production)
context = ssl._create_unverified_context()

def get_vcenter_data(vcenter, username, password):
    si = SmartConnect(host=vcenter, user=username, pwd=password, sslContext=context)
    content = si.RetrieveContent()

    esxi_data = []
    for datacenter in content.rootFolder.childEntity:
        for cluster in datacenter.hostFolder.childEntity:
            for host in cluster.host:
                license_manager = content.licenseManager
                host_license = license_manager.QueryAssignedLicenses(host=host)

                for license in host_license:
                    esxi_data.append({
                        'hostname': host.name,
                        'license': license.licenseKey,
                        'expiration_date': license.expirationDate,
                    })

    Disconnect(si)
    return esxi_data

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        vcenter = request.form['vcenter']
        username = request.form['username']
        password = request.form['password']
        try:
            esxi_data = get_vcenter_data(vcenter, username, password)
            session['esxi_data'] = esxi_data
            return render_template('index.html', esxi_data=esxi_data)
        except Exception as e:
            return str(e)  # Handle error properly in production

    return render_template('login.html')

@app.route('/download')
def download_csv():
    esxi_data = session.get('esxi_data', [])
    
    # Create a CSV file in memory
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['hostname', 'license', 'expiration_date'])
    writer.writeheader()
    writer.writerows(esxi_data)
    output.seek(0)
    
    # Send the file as a downloadable response
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='esxi_data.csv'
    )

if __name__ == '__main__':
    app.run(debug=True)
