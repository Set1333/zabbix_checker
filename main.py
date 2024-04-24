from flask import Flask, render_template, request, send_file, make_response
from pyzabbix import ZabbixAPI, ZabbixAPIException
import csv
from io import StringIO

app = Flask(__name__)

ZABBIX_URL = 'http://192.168.1.207/zabbix'
ZABBIX_USERNAME = 'Admin'
ZABBIX_PASSWORD = 'Admin'


def connect_to_zabbix():
    try:
        zabbix = ZabbixAPI(ZABBIX_URL)
        zabbix.login(ZABBIX_USERNAME, ZABBIX_PASSWORD)
        return zabbix
    except ZabbixAPIException as e:
        print(f"Failed to connect to Zabbix API: {e}")
        return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/check', methods=['POST'])
def check_server():
    ip_address = request.form['ip_address']

    zabbix = connect_to_zabbix()
    if not zabbix:
        return render_template('error.html', message='Failed to connect to Zabbix API.')

    try:
        # Check if the server is monitored
        host = zabbix.host.get(filter={'host': ip_address}, selectInterfaces='extend')
        if not host:
            return render_template('error.html', message='Server not found in Zabbix.')

        # Retrieve server name, IP address, template, elements, and triggers
        server_name = host[0]['name']
        ip_address = host[0]['interfaces'][0]['ip']
        template_name = host[0]['host']

        # Fetch elements
        elements = zabbix.item.get(hostids=host[0]['hostid'], selectItems='extend')

        # Fetch triggers
        triggers = zabbix.trigger.get(hostids=host[0]['hostid'])

        # Print fetched elements for debugging
        print("Fetched Elements:")
        for element in elements:
            print(element)

        return render_template('result.html', server_name=server_name, ip_address=ip_address,
                               template_name=template_name, elements=elements, triggers=triggers)
    except ZabbixAPIException as e:
        return render_template('error.html', message=f'Error: {e}')


@app.route('/download', methods=['POST'])
def download_info():
    server_name = request.form['server_name']
    ip_address = request.form['ip_address']
    template_name = request.form['template_name']
    elements = request.form.getlist('elements[]')
    triggers = request.form.getlist('triggers[]')

    # Create CSV data
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)

    # Write Server Information section
    csv_writer.writerow(['Server Information'])
    csv_writer.writerow(['Server Name', server_name])
    csv_writer.writerow(['IP Address', ip_address])

    # Write Template Name section
    csv_writer.writerow([])
    csv_writer.writerow(['Template Name'])
    csv_writer.writerow([template_name])

    # Write Elements section
    csv_writer.writerow([])
    csv_writer.writerow(['Elements'])
    for element in elements:
        csv_writer.writerow([element])

    # Write Triggers section
    csv_writer.writerow([])
    csv_writer.writerow(['Triggers'])
    for trigger in triggers:
        csv_writer.writerow([trigger])

    csv_data.seek(0)

    # Create response object
    response = make_response(csv_data.getvalue())

    # Set headers for file download
    response.headers['Content-Disposition'] = 'attachment; filename=server_info.csv'
    response.headers['Content-type'] = 'text/csv'

    return response


if __name__ == '__main__':
    app.run(debug=True)
