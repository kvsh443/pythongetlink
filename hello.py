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

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=port, debug=True)
