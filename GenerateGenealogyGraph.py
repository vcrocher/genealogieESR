## Generate Graph and association files from data.gouv.fr datset: https://www.data.gouv.fr/fr/datasets/theses-soutenues-en-france-depuis-1985/
## Uses theses-soutenues.csv as input and save three pickles files containing Graph and associations.
## 
## Vincent Crocher - 2022

import matplotlib.pyplot as plt
import pandas as pd
from anytree import Node, RenderTree
import networkx as nx
import mpu

#Load
filename = "theses-soutenues.csv";
theses = pd.read_csv(filename, usecols=['auteurs.0.idref',"auteurs.0.nom","auteurs.0.prenom","directeurs_these.0.idref","directeurs_these.0.nom","directeurs_these.0.prenom","directeurs_these.1.idref","directeurs_these.1.nom","directeurs_these.1.prenom","directeurs_these.2.idref","directeurs_these.2.nom","directeurs_these.2.prenom","directeurs_these.3.idref","directeurs_these.3.nom","directeurs_these.3.prenom",'date_soutenance']);

#Keep only soutenance year
theses["date_soutenance"]=pd.to_datetime(theses["date_soutenance"])
theses["date_soutenance"]=theses["date_soutenance"].dt.year

#Theses list per IDs
theses_ids = theses[['auteurs.0.idref', "directeurs_these.0.idref", "directeurs_these.1.idref","directeurs_these.2.idref","directeurs_these.3.idref", 'date_soutenance']];
theses_ids = theses_ids.rename(columns = {'auteurs.0.idref':"Aut", "directeurs_these.0.idref" :"Dir0", "directeurs_these.1.idref" :"Dir1","directeurs_these.2.idref" :"Dir2","directeurs_these.3.idref" :"Dir3", "date_soutenance":"Date"})

##People entries
tmp = theses.drop_duplicates(subset=["directeurs_these.0.idref"], ignore_index=True);
dirs0 = tmp[["directeurs_these.0.idref","directeurs_these.0.nom","directeurs_these.0.prenom"]];
dirs0 = dirs0.rename(columns={"directeurs_these.0.idref": "ID","directeurs_these.0.nom" : "Nom","directeurs_these.0.prenom": "Prenom"})
tmp = theses.drop_duplicates(subset=["directeurs_these.1.idref"], ignore_index=True);
dirs1 = tmp[["directeurs_these.1.idref","directeurs_these.1.nom","directeurs_these.1.prenom"]];
dirs1 = dirs1.rename(columns={"directeurs_these.1.idref": "ID","directeurs_these.1.nom" : "Nom","directeurs_these.1.prenom": "Prenom"})
tmp = theses.drop_duplicates(subset=["directeurs_these.2.idref"], ignore_index=True);
dirs2 = tmp[["directeurs_these.2.idref","directeurs_these.2.nom","directeurs_these.2.prenom"]];
dirs2 = dirs2.rename(columns={"directeurs_these.2.idref": "ID","directeurs_these.2.nom" : "Nom","directeurs_these.2.prenom": "Prenom"})
tmp = theses.drop_duplicates(subset=["directeurs_these.3.idref"], ignore_index=True);
dirs3 = tmp[["directeurs_these.3.idref","directeurs_these.3.nom","directeurs_these.3.prenom"]];
dirs3 = dirs3.rename(columns={"directeurs_these.3.idref": "ID","directeurs_these.3.nom" : "Nom","directeurs_these.3.prenom": "Prenom"})
dirs = pd.concat([dirs0, dirs1, dirs2, dirs3])
dirs = dirs.drop_duplicates(ignore_index=True);

tmp = theses.drop_duplicates(subset=["auteurs.0.idref"], ignore_index=True);
auteurs = tmp[['auteurs.0.idref', "auteurs.0.nom","auteurs.0.prenom", "date_soutenance"]];
auteurs = auteurs.rename(columns={'auteurs.0.idref': "ID", "auteurs.0.nom": "Nom","auteurs.0.prenom": "Prenom", "date_soutenance":"Date"})

people = pd.concat([auteurs, dirs0, dirs1, dirs2, dirs3])
people = people.drop_duplicates(subset=['ID'], ignore_index=True);


##Sanity checks
#print(dirs.tail())
#print(auteurs.tail())
#print(people.head())
display(theses_ids.tail())




##Candidates - director association table
assoc=pd.DataFrame(columns=['Dir', 'Aut']);
for l in ['Dir0', 'Dir1', 'Dir2', 'Dir3']:
    tmp = theses_ids.rename(columns={l:'Dir'});
    tmp = tmp.dropna(subset=['Dir', 'Aut']);
    tmp = tmp[['Dir', 'Aut', 'Date']]
    assoc = pd.concat([assoc, tmp], ignore_index=True);
    assoc.reset_index()
#Filter entry errors w/ candidate as director:
assoc.drop(assoc[assoc['Dir']==assoc['Aut']].index, inplace=True)


#String formatting for nicer dispaly
people["DateStr"]=people["Date"].fillna(0)
people=people.astype({'DateStr':'int'})
people["DateStr"]=people["DateStr"].apply(str)
people["DateStr"]=people["DateStr"].str.replace('^0', '?', regex=True)


#Create graph (and nice nodes)
G = nx.from_pandas_edgelist(assoc, 'Dir', 'Aut', create_using=nx.DiGraph)
mapping = dict(zip(people["ID"], people["Prenom"]+' '+people["Nom"]+'\n('+people["DateStr"]+')'));

#Save it
nx.write_gpickle(G, 'ThesesAssocGraph.gpickle')
mpu.io.write('ThesesMapping.pickle', mapping)
mpu.io.write('ThesesPeople.pickle', people)
