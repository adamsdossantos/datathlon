from pymongo import MongoClient
import json

data_appplicants ='./data/applicants.json' 
data_prospects = './data/prospects.json'
data_vagas = './data/vagas.json'

#criando client MongoDB
client = MongoClient("mongodb://root:22410Ad4m5@localhost:27017/?authSource=admin")

# creating a database MongoDB
decision_db = client['decision_db']
# creating collections MongoDB
collection_applicants = decision_db['applicants']
collection_vagas = decision_db['vagas']
collection_prospects = decision_db['prospects']

#abrindo arquivos json

with open(data_appplicants, encoding='utf-8') as f:
    raw_data_applicants = json.load(f)

with open(data_prospects, encoding='utf-8') as f:
    raw_data_prospects = json.load(f)

with open(data_vagas, encoding='utf-8') as f:
    raw_data_vagas = json.load(f)

# usando id dos arquivos para inserção na database
documents_applicants = []
for key, value in raw_data_applicants.items():
    doc = {'_id': key}
    doc.update(value)
    documents_applicants.append(doc)

documents_vagas = []
for key, value in raw_data_vagas.items():
    doc = {'_id': key}
    doc.update(value)
    documents_vagas.append(doc)

documents_prospects = []
for key, value in raw_data_prospects.items():
    doc = {'_id': key}
    doc.update(value)
    documents_prospects.append(doc)

# inserindo arquivos na database
applicant_posts = collection_applicants.insert_many(documents_applicants)
vagas_posts = collection_vagas.insert_many(documents_vagas)
applicant_prospects = collection_prospects.insert_many(documents_prospects)

print("Dados inseridos com sucesso")