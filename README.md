# Sistema de Recomendação Inteligente (ATS) - Datathon

## Tecnologias Utilizadas
- FastAPI  
- Streamlit  
- MLflow  
- Databricks  
- MongoDB  
- Qdrant  
- Sentence-Transformer  
- TF-IDF  
- Docker  
- Google Kubernetes Engine (GKE)

## Visão Geral
Projeto de recomendação inteligente com:
- API (FastAPI)
- Interface de usuário (Streamlit)
- Banco de dados em MongoDB e Qdrant
- Monitoramento de modelos com MLflow via Databricks
- Execução local via Docker Compose ou na nuvem com GKE

## Estrutura do Projeto
````bash
seu_projeto/
├── api/ # Backend FastAPI
├── streamlit_app/ # Interface com Streamlit
├── models/ # Modelos TF-IDF e SentenceTransformer
├── insertion/ # Scripts de inserção de dados
├── app/ # Módulos de conexão
├── data/ # Arquivos JSON com dados não incluídos aqui
├── docker-compose_TEST.yaml
````


## Pré-requisitos
- Docker Desktop  
- Google Cloud SDK, kubectl e Helm  
- Python, pip e uv  
- Conta GCP com permissões adequadas  
- Token Databricks 

## Instalação de dependencias

````
pip install uv
uv sync
````

## Deploy Local com Docker Compose

1. Configure variáveis e tokens em `.secrets/`
2. Verifique os arquivos `Dockerfile` e `requirements.txt`
3. Execute o comando:
```bash
docker compose -f docker-compose_TEST.yaml up --build -d
Endpoints locais:

API: http://localhost:8000

Streamlit: http://localhost:8501

Mongo Express: http://localhost:8081

Qdrant: http://localhost:6363
````
## Deploy na Nuvem com GKE

1. Criar cluster e configurar ambiente
````bash
gcloud config set project SEU_PROJETO

gcloud services enable container.googleapis.com

gcloud container clusters create meu-cluster \
  --zone southamerica-east1-b --num-nodes=1

gcloud container clusters get-credentials meu-cluster --zone southamerica-east1-b
````

2. Instalar MongoDB e Qdrant via Helm
````bash
helm repo add bitnami https://charts.bitnami.com/bitnami

helm install mongo bitnami/mongodb --set auth.rootPassword=SUA_SENHA

helm repo add qdrant https://qdrant.github.io/qdrant-helm

helm install qdrant qdrant/qdrant
````

3. Deploy da API
````bash
docker build -t gcr.io/SEU_PROJETO/sua-api:latest -f Dockerfile .

docker push gcr.io/SEU_PROJETO/sua-api:latest

kubectl apply -f kubernetes/api-deployment.yaml
````
4. População dos Dados
````bash
gcloud builds submit . --tag gcr.io/SEU_PROJETO/data-populator:latest --dockerfile insertion/Dockerfile

kubectl run mongo-pop --image=gcr.io/SEU_PROJETO/data-populator:latest --restart=Never --rm -it -- python insertion_mongodb.py

kubectl run qdrant-pop --image=gcr.io/SEU_PROJETO/data-populator:latest --restart=Never --rm -it -- python insertion_qdrant.py
````
Ou execute abra uma conexão com os banco de dados no GKE e execute a inserção de dados a partir da sua máquina (opção usada)

- Mongo DB

````bash
kubectl port-forward svc/SEU-MONGO 27017:27017
````

- Qdrant
````
kubectl port-forward svc/SEU-QDRANT 6333:6333
````
- Insira os dados.
````
python insertion/insert_mongodb.py
python insertion/insert_qdrand.py
````


5. Deploy do Streamlit
````bash
docker build -t gcr.io/SEU_PROJETO/streamlit:latest -f streamlit_app/Dockerfile .

docker push gcr.io/SEU_PROJETO/streamlit:latest

kubectl apply -f streamlit_app/streamlit-deployment.yaml
````

## Endpoints Públicos
**API**: http://34.151.203.159/

**Streamlit**: http://35.247.219.103/

**Vídeo explicativo**: https://youtu.be/-q2fPxk_mrE

## Limpeza de Recursos
```bash
gcloud container clusters delete MEU-CLIUSTER --zone southamerica-east1-b

gcloud container images delete gcr.io/SEU_PROJETO/sua-api:latest

gcloud container images delete gcr.io/SEU_PROJETO/data-populator:latest

gcloud container images delete gcr.io/SEU_PROJETO/streamlit:latest
````