this_file = "venv/bin/activate_this.py"
exec(open(this_file).read(), {'__file__': this_file})

from logging import FileHandler,WARNING
import os
from datetime import datetime
import unidecode

from flask import (
	Flask, Blueprint, flash, g, Response, redirect, render_template, request, session, url_for
)


#Needed for graphviz
os.environ["PATH"] = os.pathsep.join([os.environ.get("HOME")+'/python/bin'] + os.environ.get("PATH", "").split(os.pathsep))

# create and configure the app
application = Flask(__name__, instance_relative_config=True)
application.config.from_mapping(
	DATABASE=os.path.join(application.instance_path, 'genealogie.sqlite'),
)
file_handler = FileHandler('errorlog.txt')
file_handler.setLevel(WARNING)

# load the instance config, if it exists, when not testing
application.config.from_pyfile('config.py', silent=True)

# ensure the instance folder exists
try:
	os.makedirs(application.instance_path)
except OSError:
	pass

import db
db.init_app(application)

import search_and_graph as sg

@application.route('/download.svg', methods=('GET', 'POST'))
def serve_svg():
	if request.method == 'GET':
		if request.args.get('id'):
			aid=request.args.get('id');
			dbb = db.get_db()
			blob = dbb.execute(
				'SELECT svgGraph FROM svg WHERE ID = ?', (aid,)
			).fetchone()
			if blob is None:
				return render_template('error.html', mess="Le blob n existe pas")
			else:
				file = blob['svgGraph'].decode("utf-8")
				return Response(file, mimetype="image/svg")
		else:
			return render_template('error.html', mess="Erreur requete #1")
	else:
		return render_template('error.html', mess="Erreur requete #2")

@application.route('/', methods=('GET', 'POST'))
def index():
	if sg.data_loaded:
		if request.method == 'POST':
			if request.form['type'] == 'search':
				key = request.form['search_key'].lower()
				key=unidecode.unidecode(key)
				start_nodes, suggs=sg.find_closest_suggestions(key)
				dbb = db.get_db()
				dbb.execute(
					'INSERT INTO requetes (date, requete)'
					' VALUES (?, ?)',
					(datetime.now(), key)
				)
				dbb.commit()
				return render_template('sugg.html', suggs=zip(suggs, start_nodes))
			elif request.form['type'] == 'select':
				#returned value is the node of the suggestion
				start_node = request.form['Auteur']
				#get SVG blob
				try:
					svg_blob, cloud_svg=sg.draw_svg(start_node, start_node)
					#store svg in db
					dbb = db.get_db()
					dbb.execute(
						'REPLACE INTO svg (ID, svgGraph)'
						' VALUES (?, ?)',
						(start_node, svg_blob)
					)
					dbb.commit()
					#serve it
					svg_blob = svg_blob.decode("utf-8")
				except Exception as inst:
					return render_template('error.html', str(inst))
				return render_template('result.html', id=start_node, svg_blob=svg_blob, cloud_svg=cloud_svg)
			else:
				return render_template('index.html')
		else:
			return render_template('index.html')
	else:
		with application.app_context():
			sg.load_data()
		if(sg.data_loaded):
			return render_template('index.html')
		else:
			return render_template('error.html', mess="Données non chargées")
