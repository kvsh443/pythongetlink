from flask import Flask, render_template, request, jsonify, redirect, send_from_directory, url_for
import atexit
import os
import json
from ibm_botocore.client import Config
import ibm_boto3
from os import path
import requests
import re
import string
import random

this_path = os.getcwd()

UPLOAD_FOLDER = '/static/'

app = Flask(__name__, static_url_path='')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# On IBM Cloud Cloud Foundry, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))
#
try:
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
except:
    print("Unable to access ibm_boto3.{0} terminating the program".format(__name__))

def download_item(bucket_name, item_name, path):
    print("Downloading item from the bucket: {0}, key: {1}".format(bucket_name, item_name))
    file_path = this_path+UPLOAD_FOLDER+path
    try:
        cos.meta.client.download_file(bucket_name, item_name, file_path)
        print("File contents: {0} added to {1}".format(item_name,file_path))
        return(file_path)
    except Exception as e:
        print("Unable to download file contents: {0}".format(e))

def upload_item(bucket_name, path, item_name):
    print("Uploading item from the bucket: {0}, key: {1}".format(bucket_name, item_name))
    file_path = this_path+UPLOAD_FOLDER+path
    try:
        cos.meta.client.upload_file(file_path, bucket_name, item_name)
        print("File contents: {0} added to {1}".format(item_name,bucket_name))
        return file_path
    except Exception as e:
        print("Unable to Upload file contents: {0}".format(e))


def rename_file(file_path,item_name,filename):
    new_file_path = this_path+UPLOAD_FOLDER+filename
    os.rename(file_path,new_file_path)
    return new_file_path

def id_gen(size=8, chars=string.ascii_uppercase + string.digits):
    return (''.join(random.choice(chars) for _ in range(size)))

def url_response(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    return requests.get(url, headers=headers, allow_redirects=True, stream=True)

def filename_via_cd(cd):
    fname = re.findall('filename(.+)',cd)
    if len(fname) == 0:
        return None
    return fname[0]

def filename_via_url(url):
    if url.find('/'):
        return url.rsplit('/',1)[1]

def filename_random():
        return (id_gen()+"no.xt")

@app.route('/')
def root():
    return redirect("https://kvsh443.github.io/")

@app.route('/hello')
def hello_world():
    return app.send_static_file('rindex.html')

@app.route('/data', methods=['GET'])
def file_s3():
    file = request.args.get('file')
    path = file
    filepath = download_item("kvsh",file,path)
    out = "File Name on s3:{0} \n File Name on Server: {1}".format(file,filepath)
    print(out)
    return (out)
    #return send_from_directory(app.config['UPLOAD_FOLDER'],file)

@app.route('/ren', methods=['GET'])
def file_s3_rename():
    file = request.args.get('file')
    path = "/"+file
    newname= request.args.get('new')
    filepath = rename_file(download_item("kvsh",file,path),file,newname)
    out = "File Name on s3:{0} \n File Name on Server: {1}".format(file,filepath)
    print(out)
    return (out)

@app.route('/renu', methods=['GET'])
def file_s3file_s3_rename_upload():
    file = request.args.get('file')
    path ="/"+file
    new = request.args.get('new')
    filepath = ("kvsh",(rename_file(download_item("kvsh",file,path),file,new)),new) #keep the renamed file in the server an upload the new file to s3
    out = ("File Name on s3:{0} \n File Name on Server: {1}".format(file,filepath))
    print(out)
    return (out)

@app.route('/link', methods=['GET'])
def download_from_link():
    url = request.args.get('url')
    type = request.args.get('type')
    if type == '2':
        name = filename_via_cd(url_response(url).headers.get('content-disposition'))
    elif type == '1':
        name = filename_via_url(url)
    elif type == '0':
        name = request.args.get('name')
    else:
        name = filename_random()
    file = this_path+UPLOAD_FOLDER+name
    try:
        with open(file,'wb') as f:
            for chunk in url_response(url).iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
    except:
        print(file+" writing unsuccessful! ")
    out = "Downloaded from:- {0} as file name:- {1} path:- {2}".format(url, name ,file)
    print(out)
    return (out)

@atexit.register
def shutdown():
    if client:
        client.disconnect()

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=port, debug=True)
