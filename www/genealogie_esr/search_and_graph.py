import pandas as pd
import networkx as nx
import mpu
from rapidfuzz import fuzz, process
import os

import db


G=[] #Main graph
mapping_d={} #Dict use to map ID with display formatting of the nodes (nom prenom date)
search_d={} #Dict of search
data_loaded=False

## Extract a given field from pd
def get_this(indf, field, wherethisone, isthis):
	tmp=indf[indf[wherethisone]==isthis];
	return tmp.at[tmp.index[0], field];

## Find closest possible names and associated ids
def find_closest_suggestions(search):
	options=process.extract(search, search_d, limit=5)
	pids=[]
	suggs=[]
	dbb = db.get_db()
	for o in options:
		pids.append(o[2])
		suggs.append(mapping_d[o[2]].replace('\\n', ' (')+')')
	return pids, suggs

def get_display_from_id(dbb, id):
	ret=dbb.execute('SELECT Prenom, Nom, DateStr FROM people WHERE ID = ?', (id,)).fetchone()
	return ret['Prenom']+" "+ret['Nom']+'\\n'+ret['DateStr']

## Subgrah around given node
def get_subgraph(start_node):
	Gd=nx.bfs_tree(G, start_node) #Get nodes downwards only
	nx.set_node_attributes(Gd, 'etud', name='class') #class are used for SVG style
	nx.set_edge_attributes(Gd, 'etud', name='class') #class are used for SVG style
	Gu=nx.bfs_tree(G, start_node, reverse=True) #Get nodes upwards only
	nx.set_node_attributes(Gu, 'dir', name='class')
	G2=nx.compose(Gd,Gu.reverse()) #Merge both
	for gu in Gu: #For each upward, get downwards nodes
		G3=nx.bfs_tree(G, gu)
		G3=nx.compose(G2,G3) #Merge
	nx.set_node_attributes(G3, {start_node: 'auteur'}, name='class') #class are used for SVG style
	#dbb = db.get_db()
	#G3=nx.relabel_nodes(G3, lambda id: get_display_from_id(dbb, id), copy=False) #With db: slow
	G3=nx.relabel_nodes(G3, mapping_d, copy=False)
	return G3

## Format for agraph
def agraph_format(g, start_node):
	A = nx.nx_agraph.to_agraph(g)
	A.layout('dot', args='-Nfontsize=12 -Nwidth=".2" -Nheight="1." -Nmargin=0.1 -Gfontsize=8')
	return A

## To neat SVG
def draw_svg(start_node, name):
	g=get_subgraph(start_node)
	A = agraph_format(g, start_node)
	return A.draw(path=None, format='svg')

## Load data
def load_data():
	global G, data_loaded, search_d, mapping_d
	try: 
		G = nx.read_gpickle(os.path.abspath(os.path.dirname(__file__)) + '/data/ThesesAssocGraph.gpickle')
	except FileNotFoundError:
		data_loaded=False
		raise FileNotFoundError("Can't load the files")
	# Create search list from db
	dbb = db.get_db()
	#search_l = [item['Recherche'] for item in dbb.execute('SELECT Recherche FROM people').fetchall()]
	res=dbb.execute('SELECT ID,Prenom,Nom,DateStr,Recherche FROM people').fetchall()
	#Mapping between ID and display name
	mapping_d={};
	search_d={};
	for row in res:
		if(type(row['Prenom'])==str and type(row['Nom'])==str and type(row['DateStr'])==str):
			mapping_d[row['ID']]=row['Prenom']+" "+row['Nom']+'\\n'+row['DateStr']
			search_d[row['ID']]=row['Recherche']
	data_loaded=True