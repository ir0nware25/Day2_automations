from flask import Flask, request, jsonify
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl

app = Flask(__name__)

def get_vcenter_connection(host, user, pwd, port=443):
    # Disable SSL certificate verification
    context = ssl._create_unverified_context()

    # Connect to vCenter
    service_instance = SmartConnect(
        host=host,
        user=user,
        pwd=pwd,
        port=port,
        sslContext=context
    )
    return service_instance

def get_esxi_licenses(service_instance):
    content = service_instance.RetrieveContent()
    license_manager = content.licenseManager
    licenses = license_manager.licenses

    license_info = []
    for lic in licenses:
        license_info.append({
            'License Key': lic.licenseKey,
            'Name': lic.name,
            'Edition': lic.editionKey
        })

    return license_info

@app.route('/get_licenses', methods=['POST'])
def get_licenses():
    data = request.json
    vcenter_host = data.get('vcenter_host')
    vcenter_user = data.get('vcenter_user')
    vcenter_password = data.get('vcenter_password')

    if not vcenter_host or not vcenter_user or not vcenter_password:
        return jsonify({"error": "Please provide vCenter host, user, and password"}), 400

    try:
        # Establish connection to vCenter
        service_instance = get_vcenter_connection(vcenter_host, vcenter_user, vcenter_password)
        licenses = get_esxi_licenses(service_instance)

        # Disconnect from vCenter
        Disconnect(service_instance)

        return jsonify(licenses)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
# ```
