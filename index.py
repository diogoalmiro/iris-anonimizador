#!/BackupDisk_Raid1/bak_home/dalmiro/anonimizador/env/bin/python3
from flask import Flask, request, Response, jsonify, send_from_directory
from flask_cors import CORS
import os
import tempfile
import csv
import subprocess

app = Flask(__name__, static_folder="build")
CORS(app)

@app.route("/", methods=["POST"])
def handle_post():
	_, file_extension = os.path.splitext(request.files["file"].filename)
	uploaded_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False)
	request.files["file"].save(uploaded_file)
	uploaded_file.flush()
	uploaded_file.close()

	#caixa preta
	resp = subprocess.Popen(f"python black-box-cli.py {uploaded_file.name}", shell=True, stdout=subprocess.PIPE).stdout.read()
	os.unlink(uploaded_file.name)
	return resp

@app.route("/html", methods=["POST"])
def handle_post_html():
	_, file_extension = os.path.splitext(request.files["file"].filename)
	uploaded_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False)
	request.files["file"].save(uploaded_file)
	uploaded_file.flush()
	uploaded_file.close()

	#caixa preta
	resp = subprocess.Popen(f"python black-box-cli.py {uploaded_file.name} --html-only", shell=True, stdout=subprocess.PIPE).stdout.read()
	os.unlink(uploaded_file.name)
	return resp

@app.route("/types", methods=["GET"])
def get_types():
	typesset = set(["ORG", "LOC", "PES", "DAT"]) # NER types
	with open('patterns.csv', 'r') as csvfd:
		reader = csv.DictReader(csvfd, delimiter="\t")
		for r in reader:
			typesset.add(r['Label'])
	return jsonify(list(typesset))

@app.route('/', methods=["GET"], defaults={'path': ''})
@app.route('/<path:path>', methods=["GET"])
def send_report(path=None):
	if path is None:
		path = "index.html"
	try:
		return send_from_directory('build', path)
	except Exception as e:
		print(e)
		return send_from_directory('build', "index.html")

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=7999)
