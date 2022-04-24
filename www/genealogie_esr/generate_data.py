## Generate Graph and association files from data.gouv.fr datset: https://www.data.gouv.fr/fr/datasets/theses-soutenues-en-france-depuis-1985/
## Uses theses-soutenues.csv as input and save three pickles files containing Graph and associations.
## 
## Vincent Crocher - 2022

import os
import pandas as pd
import networkx as nx
import mpu
import unidecode

#Load
filename = os.path.abspath(os.path.dirname(__file__)) + '/data/theses-soutenues.csv';
theses = pd.read_csv(filename, 
			usecols=['auteurs.0.idref',"auteurs.0.nom","auteurs.0.prenom","directeurs_these.0.idref","directeurs_these.0.nom","directeurs_these.0.prenom","directeurs_these.1.idref","directeurs_these.1.nom","directeurs_these.1.prenom","directeurs_these.2.idref","directeurs_these.2.nom","directeurs_these.2.prenom","directeurs_these.3.idref","directeurs_these.3.nom","directeurs_these.3.prenom",'date_soutenance','titres.fr','titres.en'],
			dtype=str);

#Keep only soutenance year
theses["date_soutenance"]=pd.to_datetime(theses["date_soutenance"])
theses["date_soutenance"]=theses["date_soutenance"].dt.year

#Theses list per IDs
theses_ids = theses[['auteurs.0.idref', "directeurs_these.0.idref", "directeurs_these.1.idref","directeurs_these.2.idref","directeurs_these.3.idref", 'date_soutenance']];
theses_ids = theses_ids.rename(columns = {'auteurs.0.idref':"Aut", "directeurs_these.0.idref" :"Dir0", "directeurs_these.1.idref" :"Dir1","directeurs_these.2.idref" :"Dir2","directeurs_these.3.idref" :"Dir3", "date_soutenance":"Date"})

##People entries
dirs=pd.DataFrame(columns=['ID','Nom', 'Prenom', 'TitreThese', 'TitreTheseEN']);
for l in ['0', '1', '2', '3']:
	tmp = theses.drop_duplicates(subset=['directeurs_these.'+l+'.idref'], ignore_index=True);
	tmp = tmp[['directeurs_these.'+l+'.idref','directeurs_these.'+l+'.nom','directeurs_these.'+l+'.prenom']];
	tmp = tmp.rename(columns={'directeurs_these.'+l+'.idref': "ID",'directeurs_these.'+l+'.nom': "Nom",'directeurs_these.'+l+'.prenom': "Prenom"})
	dirs = pd.concat([dirs, tmp], ignore_index=True);
	dirs.reset_index()
dirs = dirs.drop_duplicates(ignore_index=True);
dirs['TitreThese']='-';
dirs['TitreTheseEN']='-';

tmp = theses.drop_duplicates(subset=["auteurs.0.idref"], ignore_index=True);
aut = tmp[['auteurs.0.idref', "auteurs.0.nom", "auteurs.0.prenom", "date_soutenance", 'titres.fr', 'titres.en']];
aut = aut.rename(columns={'auteurs.0.idref': "ID", "auteurs.0.nom": "Nom","auteurs.0.prenom": "Prenom", "date_soutenance":"Date", 'titres.fr': "TitreThese", 'titres.en': "TitreTheseEN"})

people = pd.concat([aut, dirs])
people = people.drop_duplicates(subset=['ID'], ignore_index=True);


##Sanity checks
#print(dirs.tail())
#print(auteurs.tail())
#print(theses_ids.tail())
print(people.tail())

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


#String formatting for nicer display
people["Prenom"]=people["Prenom"].fillna("") #Curate people w/ no Prenom
people["DateStr"]=people["Date"].fillna(0)
people=people.astype({'DateStr':'int'})
people["DateStr"]=people["DateStr"].apply(str)
people["DateStr"]=people["DateStr"].str.replace('^0', '?', regex=True)
people["TitreThese"]=people["TitreThese"].fillna("-")
people["TitreTheseEN"]=people["TitreTheseEN"].fillna("-")
people["Recherche"]=people["Prenom"]+' '+people["Nom"]
people["Recherche"]=people["Recherche"].str.lower()
people["Recherche"]=people["Recherche"].apply(lambda x: unidecode.unidecode(x) if (type(x)==str) else x) 

print(people.head(15))
print(people.tail(15))

#Create graph and save to pickle file
G = nx.from_pandas_edgelist(assoc, 'Dir', 'Aut', create_using=nx.DiGraph)
nx.write_gpickle(G, os.path.abspath(os.path.dirname(__file__)) + '/data/ThesesAssocGraph.gpickle')

#Populate db with people
def load_people_table(db):
	people.to_sql('people', db, index=False, if_exists='append')
