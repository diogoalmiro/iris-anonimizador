#!/BackupDisk_Raid1/bak_home/dalmiro/anonimizador/env/bin/python3
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import os
import tempfile
import pypandoc
import re
from specific_spacy import nlp
import csv

app = Flask(__name__)
CORS(app)


class EntPool:
	def __init__(self):
		self.pool = dict()
		self.counts = dict()
	
	def add(self, ent):
		if ent.text not in self.pool:
			self.pool[ent.text] = ent
			self.counts[ent.text] = dict();
			self.counts[ent.text][ent.label_] = 1;
			return True
		else:
			if ent.label_ not in self.counts[ent.text]:
				self.counts[ent.text][ent.label_] = 0;
			self.counts[ent.text][ent.label_] += 1;
		
		if self.pool[ent.text].label_ != ent.label_:
			print( f"WARNING: Entities with same text but different labels {ent.text} {ent.label_} {self.pool[ent.text].label_}" )

def dynamicspaces(match):
	return " "*(match.end()-match.start())

def process_html(html, entpool: EntPool):
	original = re.sub(r"\n", "", html)
	notags = re.sub(r"<[^>]*>", dynamicspaces, original)
	doc = nlp(notags)
	merge = ""
	lastI = 0
	c=0
	for ent in doc.ents:
		entpool.add(ent)
		merge += original[lastI:ent.start_char]
		merge += f"<mark role={ent.label_}>{original[ent.start_char:ent.end_char]}</mark>"
		lastI = ent.end_char
	merge += original[lastI:]
	return merge

def process_simple_line(line, entpool: EntPool):
	doc = nlp(line)
	lastI = 0
	rline = ""
	for ent in doc.ents:
		rline += line[lastI:ent.start_char]
		rline += f"<mark role={ent.label_}>{ent.text}</mark>"
		lastI = ent.end_char
		entpool.add(ent)
	rline += line[lastI:]
	return rline

@app.route("/",methods=["GET"])
def send_index():
	return """
<!DOCTYPE html>
	<html lang="en">
		<head>
			<meta charset="UTF-8">
			<meta http-equiv="X-UA-Compatible" content="IE=edge">
			<meta name="viewport" content="width=device-width, initial-scale=1.0">
		</head>
		<body>
			<h3>Interface testes anonimizador</h3>
			<h4>Input</h4>
			<form class="col-12 col-sm-6" id="anonim-form" action="http://localhost:7998/" method="post">
				<input type="file" name="file"><button type="submit">Correr a partir de ficheiro</button></form>
			<form class="col-12 col-sm-6" id="anonim-form-text" action="http://localhost:7998/" method="post">
				<textarea class="w-100" name="file"></textarea>
				<button type="submit">Correr este texto</button>
			</form>
			<h4>Output</h4>
			<div id="out"></div>
			<style>
				mark::before{
					content: attr(role);
					font-size: 0.5rem;
					font-weight: bold;
					padding: 0.2rem;
				}
			</style>
			<script>
	document.getElementById("anonim-form").addEventListener("submit", (evt) => {
    evt.preventDefault();
    let button = document.getElementById("anonim-form").querySelector("button");
    button.disabled = true;
    let formData = new FormData(document.getElementById("anonim-form"));
    fetch("./", {
        method: "POST",
        body: formData
    }).then(response => response.text()).then(text => {
        document.getElementById("out").innerHTML = text;
        button.disabled = false;
    });
});
document.getElementById("anonim-form-text").addEventListener("submit", (evt) => {
    evt.preventDefault();
    let button = document.getElementById("anonim-form-text").querySelector("button");
    button.disabled = true;
    let formData = new FormData();
    formData.append("file", new Blob([document.getElementById("anonim-form-text").querySelector("textarea").value]), "text.txt");
    fetch("./", {
        method: "POST",
        body: formData
    }).then(response => response.text()).then(text => {
        document.getElementById("out").innerHTML = text;
        button.disabled = false;
    });
});
			</script>
		</body>
	</html>
"""

@app.route("/", methods=["POST"])
def handle_post():
	_, file_extension = os.path.splitext(request.files["file"].filename)
	uploaded_file = tempfile.NamedTemporaryFile(suffix=file_extension)
	request.files["file"].save(uploaded_file)
	uploaded_file.flush()
	ents = EntPool()
	result = ""
	if not file_extension == ".txt":
		html = pypandoc.convert_file(uploaded_file.name, "html", extra_args=["--wrap","none"])
		result = process_html(f"<div data-from={file_extension}>{html}</div>", ents)
	else:
		uploaded_file.seek(0)
		result = f"<div data-from={file_extension}>"
		for line in uploaded_file.readlines():
			result += "<p>"
			result += process_simple_line(line.decode("utf-8"), ents)
			result += "</p>"
		result += "</div>"

	result += f"<table><tr><th>Entity</th><th>Label(s)</th></tr>"
	for ent in ents.pool.values():
		result += f'<tr><td>{ent.text}</td><td>{" ".join(f"{o[0]} ({o[1]})" for o in ents.counts[ent.text].items())}</td></tr>'
	return Response(result,  mimetype='text/html')

@app.route("/html", methods=["POST"])
def handle_post_html():
	_, file_extension = os.path.splitext(request.files["file"].filename)
	uploaded_file = tempfile.NamedTemporaryFile(suffix=file_extension)
	request.files["file"].save(uploaded_file)
	uploaded_file.flush()
	ents = EntPool()
	result = ""
	if not file_extension == ".txt":
		html = pypandoc.convert_file(uploaded_file.name, "html", extra_args=["--wrap","none"])
		result = f"<div data-from={file_extension}>{html}</div>"
	else:
		uploaded_file.seek(0)
		result = f"<div data-from={file_extension}>"
		for line in uploaded_file.readlines():
			result += "<p>"
			result += line.decode("utf-8")
			result += "</p>"
		result += "</div>"

	result += f"<table><tr><th>Entity</th><th>Label</th></tr>"
	return Response(result,  mimetype='text/html')

@app.route("/types", methods=["GET"])
def get_types():
	typesset = set(["ORG", "LOC", "PES", "DAT"]) # NER types
	with open('patterns.csv', 'r') as csvfd:
		reader = csv.DictReader(csvfd, delimiter="\t")
		for r in reader:
			typesset.add(r['Label'])
	return jsonify(list(typesset))

if __name__ == '__main__':
	app.run(host='0.0.0.0',port=7999)