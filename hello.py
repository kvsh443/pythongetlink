from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify, redirect, send_from_directory, url_for
import atexit
import os
import json
from ibm_botocore.client import Config
import ibm_boto3
from werkzeug.utils import secure_filename
from os import path

this_path = os.getcwd()

UPLOAD_FOLDER = '/static/'

app = Flask(__name__, static_url_path='')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db_name = 'mydb'
client = None
db = None

if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif "CLOUDANT_URL" in os.environ:
    client = Cloudant(os.environ['CLOUDANT_USERNAME'], os.environ['CLOUDANT_PASSWORD'], url=os.environ['CLOUDANT_URL'], connect=True)
    db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On IBM Cloud Cloud Foundry, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))
#

api_key = os.environ['cos_api_key']
service_instance_id = os.environ['cos_resource_instance_id']
auth_endpoint = 'https://iam.bluemix.net/oidc/token'
service_endpoint = 'https://s3.us-east.objectstorage.softlayer.net'
cos = ibm_boto3.resource('s3',
                      ibm_api_key_id=api_key,
                      ibm_service_instance_id=service_instance_id,
                      ibm_auth_endpoint=auth_endpoint,
                      config=Config(signature_version='oauth'),
                      endpoint_url=service_endpoint)
def download_item(bucket_name, item_name, path):
    print("Downloading item from the bucket: {0}, key: {1}".format(bucket_name, item_name))
    file_path = this_path+UPLOAD_FOLDER+path
    try:
        cos.meta.client.download_file(bucket_name, item_name, file_path)
        print("File contents: {0} added to {1}".format(item_name,file_path))
        return(file_path)
    except Exception as e:
        print("Unable to download file contents: {0}".format(e))

@app.route('/')
def root():
    return redirect("https://kvsh443.github.io/")

@app.route('/hello')
def hello_world():
    return app.send_static_file('index.html')

@app.route('/data', methods=['GET'])
def file_s3():
    file = request.args.get('file')
    path = "/"+file
    filepath = download_item("kvsh",file,path)
    print("File Name on s3:{0} \n File Name on Server: {1}".format(file,filepath))
    out = "File Name on s3:{0} \n File Name on Server: {1}".format(file,filepath)
    return (out)
    #return send_from_directory(app.config['UPLOAD_FOLDER'],file)


# /* Endpoint to greet and add a new visitor to database.
# * Send a POST request to localhost:8000/api/visitors with body
# * {
# *     "name": "Bob"
# * }
# */
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:
        return jsonify(list(map(lambda doc: doc['name'], db)))
    else:
        print('No database')
        return jsonify([])

# /**
#  * Endpoint to get a JSON array of all the visitors in the database
#  * REST API example:
#  * <code>
#  * GET http://localhost:8000/api/visitors
#  * </code>
#  *
#  * Response:
#  * [ "Bob", "Jane" ]
#  * @return An array of all the visitor names
#  */
@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    data = {'name':user}
    if client:
        my_document = db.create_document(data)
        data['_id'] = my_document['_id']
        return jsonify(data)
    else:
        print('No database')
        return jsonify(data)

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=port, debug=True)
