## Set of fucntions to manipulate, search in, graph and generate point clouds from the theses database  
## 
## Part of GenealogieESR 
## 
## Vincent Crocher - 2022

import pandas as pd
import networkx as nx
import mpu
from rapidfuzz import fuzz, process
import os
from wordcloud import WordCloud

#import db #For online use
from . import db  #For local use only


G=[] #Main graph
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
        #suggs.append(mapping_d[o[2]].replace('\\n', ' (')+')')
        suggs.append(get_display_from_id(dbb, o[2]).replace('\\n', ' (')+')')
    return pids, suggs

## Return formatted string for each person to dispay (on node or list)
def get_display_from_id(dbb, id):
    ret=dbb.execute('SELECT Prenom, Nom, DateStr FROM people WHERE ID = ?', (id,)).fetchone()
    return ret['Prenom']+" "+ret['Nom']+'\\n'+ret['DateStr']

## Return theses title from id
def get_title_from_id(dbb, id):
    ret=dbb.execute('SELECT TitreThese FROM people WHERE ID = ?', (id,)).fetchone()
    if(ret['TitreThese']=='-'):
        ret=dbb.execute('SELECT TitreTheseEN FROM people WHERE ID = ?', (id,)).fetchone()
        return ret['TitreTheseEN']
    else:
        return ret['TitreThese']

## To generate a word cloud from thesis titles
def words_cloud(sub_g):
    exclude_l = ['-', 'à', 'le', 'la', 'les', 'des', 'un', 'une', 'de', 'du', "d", "l", "et", "ou", "en", "sa", "son", "ses", "leur",
                'sur', 'dans', 'au', 'aux', 'par', 'pour', 'chez', 'avec',
                'contribution', 'contributions', 'étude', 'études', 'essais', 'etude', 'etudes',
                'in', 'of', 'the', 'a', 'an', 'and', 'or', 'for', 'on', 'about', 'with',
                'essay', 'essays', 'study', 'studies'];
    text=""
    dbb = db.get_db()
    for n in sub_g.nodes:
        titre = get_title_from_id(dbb, n) #To optimise: using same request as for graph
        titre=titre.replace("'", ' ')
        titre=titre.lower()
        text=text+' '+titre
    wordcloud = WordCloud(stopwords = exclude_l,collocations=True,background_color="white",width=700,height=400).generate(text)
    return wordcloud.to_svg()

## Subgrah around given node
def get_subgraph(start_node, cloud):
    Gd=nx.bfs_tree(G, start_node) #Get nodes downwards only
    nx.set_node_attributes(Gd, 'etud', name='class') #class are used for SVG style
    nx.set_edge_attributes(Gd, 'etud', name='class') #class are used for SVG style
    Gu=nx.bfs_tree(G, start_node, reverse=True) #Get nodes upwards only
    nx.set_node_attributes(Gu, 'dir', name='class') #class are used for SVG style
    nx.set_edge_attributes(Gu, 'dir', name='class') #class are used for SVG style
    G2=nx.compose(Gd,Gu.reverse()) #Merge both
    for gu in Gu: #For each upward, get downwards nodes: sibblings
        G3=nx.bfs_tree(G, gu)
        G3=nx.compose(G2,G3) #Merge
    
    #Generate words cloud if needed
    if(cloud):
        cloud_svg = words_cloud(G3);
    else:
        cloud_svg = "";
    
    #Nicely name and tag nodes
    nx.set_node_attributes(G3, {start_node: 'auteur'}, name='class') #class are used for SVG style
    dbb = db.get_db()
    for node in G3.nodes:
        nx.set_node_attributes(G3,{node: get_title_from_id(dbb, node)}, name='tooltip') #class are used for SVG style
    G3=nx.relabel_nodes(G3, lambda id: get_display_from_id(dbb, id), copy=False) #With db
    #G3=nx.relabel_nodes(G3, mapping_d, copy=False)
    return G3, cloud_svg

## Format for agraph
def agraph_format(g, start_node):
    A = nx.nx_agraph.to_agraph(g)
    A.layout('dot', args='-Nfontsize=12 -Nwidth=".2" -Nheight="1." -Nmargin=0.1 -Gfontsize=8')
    return A

## To neat SVG (and wordcloud)
def draw_svg(start_node, name):
    g, cloud_svg = get_subgraph(start_node, cloud=True)
    A = agraph_format(g, start_node)
    return A.draw(path=None, format='svg'), cloud_svg

## Load graph data from gpickle file and search fields from db 
def load_data():
    global G, data_loaded, search_d
    try: 
        G = nx.read_gpickle(os.path.abspath(os.path.dirname(__file__)) + '/data/ThesesAssocGraph.gpickle')
    except FileNotFoundError:
        data_loaded=False
        raise FileNotFoundError("Can't load the files")
    try: 
        # Create search list from db
        dbb = db.get_db()
        res=dbb.execute('SELECT ID,Recherche FROM people').fetchall()
        search_d={};
        for row in res:
            if(type(row['Recherche'])==str):
                search_d[row['ID']]=row['Recherche']
        data_loaded=True
    except Exception as e:
        data_loaded=False