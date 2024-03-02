## Generate Graph and association files from data.gouv.fr datset: https://www.data.gouv.fr/fr/datasets/theses-soutenues-en-france-depuis-1985/
## Uses theses-soutenues.csv as input and save a pickle file containing Graph and associations and can populate a db
## 
## Vincent Crocher - 2022 - 2024

import pandas as pd
import networkx as nx
import pickle
import mpu
import unidecode

#Load
filename = "../theses-soutenues.csv";
theses = pd.read_csv(filename, 
            usecols=['auteur.idref',"auteur.nom","auteur.prenom","directeurs_these.0.idref","directeurs_these.0.nom","directeurs_these.0.prenom","directeurs_these.1.idref","directeurs_these.1.nom","directeurs_these.1.prenom","directeurs_these.2.idref","directeurs_these.2.nom","directeurs_these.2.prenom","directeurs_these.3.idref","directeurs_these.3.nom","directeurs_these.3.prenom",'date_soutenance','titres.fr','titres.en'],
            dtype=str);

#Keep only soutenance year
theses["date_soutenance"]=pd.to_datetime(theses["date_soutenance"], format='%Y-%m-%d', exact=False)
theses["date_soutenance"]=theses["date_soutenance"].dt.year

#Theses list per IDs
theses_ids = theses[['auteur.idref', "directeurs_these.0.idref", "directeurs_these.1.idref","directeurs_these.2.idref","directeurs_these.3.idref", 'date_soutenance']];
theses_ids = theses_ids.rename(columns = {'auteur.idref':"Aut", "directeurs_these.0.idref" :"Dir0", "directeurs_these.1.idref" :"Dir1","directeurs_these.2.idref" :"Dir2","directeurs_these.3.idref" :"Dir3", "date_soutenance":"Date"})

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

tmp = theses.drop_duplicates(subset=["auteur.idref"], ignore_index=True);
aut = tmp[['auteur.idref', "auteur.nom", "auteur.prenom", "date_soutenance", 'titres.fr', 'titres.en']];
aut = aut.rename(columns={'auteur.idref': "ID", "auteur.nom": "Nom","auteur.prenom": "Prenom", "date_soutenance":"Date", 'titres.fr': "TitreThese", 'titres.en': "TitreTheseEN"})

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


#Create graph (and nice nodes)
G = nx.from_pandas_edgelist(assoc, 'Dir', 'Aut', create_using=nx.DiGraph)
mapping = dict(zip(people["ID"], people["Prenom"]+' '+people["Nom"]+'\n('+people["DateStr"]+')'));

#Save it
with open('ThesesAssocGraph.gpickle', 'wb') as f:
    pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)
mpu.io.write('ThesesMapping.pickle', mapping)
mpu.io.write('ThesesPeople.pickle', people)
