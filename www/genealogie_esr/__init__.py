import os
from datetime import datetime
import unidecode

from flask import (
	Flask, Blueprint, flash, g, Response, redirect, render_template, request, session, url_for
)


def create_app(test_config=None):
	# create and configure the app
	app = Flask(__name__, instance_relative_config=True)
	app.config.from_mapping(
		DATABASE=os.path.join(app.instance_path, 'genealogie.sqlite'),
	)

	if test_config is None:
		# load the instance config, if it exists, when not testing
		app.config.from_pyfile('config.py', silent=True)
	else:
		# load the test config if passed in
		app.config.from_mapping(test_config)

	# ensure the instance folder exists
	try:
		os.makedirs(app.instance_path)
	except OSError:
		pass

	from . import db
	db.init_app(app)
	
	from . import search_and_graph as sg

	@app.route('/download.svg', methods=('GET', 'POST'))
	def serve_svg():
		if request.method == 'GET':
			if request.args.get('id'):
				aid=request.args.get('id');
				dbb = db.get_db()
				blob = dbb.execute(
					'SELECT svgGraph FROM svg WHERE ID = ?', (aid,)
				).fetchone()
				if blob is None:
					return render_template('error.html')
				else:
					file = blob['svgGraph'].decode("utf-8")
					return Response(file, mimetype="image/svg")
			else:
				return render_template('error.html')
		else:
			return render_template('error.html')

	@app.route('/', methods=('GET', 'POST'))
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
					return render_template('result.html', id=start_node, svg_blob=svg_blob, cloud_svg=cloud_svg)
				else:
					return render_template('index.html')
			else:
				return render_template('index.html')
		else:
			with app.app_context():
				sg.load_data()
			if(sg.data_loaded):
				return render_template('index.html')
			else:
				return render_template('error.html')

	return app