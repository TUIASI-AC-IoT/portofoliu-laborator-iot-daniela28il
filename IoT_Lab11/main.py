from datetime import datetime
from os.path import join, exists
from time import strftime

from flasgger import Swagger
from flask import Flask, request, jsonify
import os
import uuid

app = Flask(__name__)
swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "File Management API",
        "description": "A simple RESTful API for managing files.",
        "version": "1.0.0"
    },
    "basePath": "/"
})

BASE_DIR = './files'

if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

@app.route('/files', methods=['GET'])
def list_files():
    """
    List all files in the directory.
    ---
    tags:
      - Files
    responses:
      200:
        description: A list of filenames
        schema:
          type: array
          items:
            type: string
    """
    return jsonify(os.listdir(BASE_DIR))

@app.route('/files/<filename>', methods=['GET'])
def read_file(filename):
    rsp = {}
    filepath = join(BASE_DIR, filename)
    if exists(filepath):
        rsp["path"] = filepath
        stats = os.stat(filepath)
        rsp["size"] = stats.st_size
        with open(filepath) as f:
            rsp["content"] = f.read()
    else:
        rsp["status"] = "NOK"
        rsp["err_msg"] = "File not found."
    return jsonify(rsp)

@app.route('/files', methods=['POST', 'PUT'])
def create_file():
    rsp = {}
    filepath = ''
    req = request.get_json()
    if request.method == 'POST':
        filepath = join(BASE_DIR, strftime("%Y%m%d_%H%M%S.txt"))
    elif request.method == 'PUT':
        filepath = join(BASE_DIR, req["name"])
    with open(filepath, "w") as f:
        f.write(req["content"])
    rsp["status"] = "OK"
    rsp["filename"] = filepath.split('/')[-1]
    return jsonify(rsp)

@app.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        os.remove(os.path.join(BASE_DIR, filename))
        return 'File deleted', 200
    except FileNotFoundError:
        return 'File not found', 404

@app.route('/files/<filename>', methods=['PUT'])
def update_file(filename):
    data = request.get_json()
    content = data.get('content', '')
    try:
        with open(os.path.join(BASE_DIR, filename), 'w') as f:
            f.write(content)
        return 'File updated', 200
    except FileNotFoundError:
        return 'File not found', 404

if __name__ == '__main__':
    app.run(debug=True)
