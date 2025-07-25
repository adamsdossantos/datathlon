# Datathlon Projeto de Sistema de Recomendação Inteligente (ATS)

## **Estrutura Tecnologica** 
- FastAPI
- Streamlit
- MLflow
- MongoDB
- Qdrant
- Sentence-Transformer
- TD-IDF
- GKE
- Docker

## **Introdução**
Este projeto implementa um sistema de recomendação inteligente com uma API de backend, um frontend Streamlit para experiência do usuário (UX), e integração com MLflow hospedada no Databricks para monitoramento de modelos, MongoDB para dados brutos e Qdrant para busca vetorial.

A arquitetura do projeto permite o deploy tanto localmente com Docker Compose quanto em ambiente de nuvem com Google Kubernetes Engine (GKE).

## **Estrutura do Projeto**

```bash
seu_projeto_principal/
├── api/
│   ├── Dockerfile             # Dockerfile para o serviço da API
│   ├── main.py                # Ponto de entrada da API (FastAPI)
│   ├── utils.py               # Funções utilitárias da API
│   └── requirements.txt       # Dependências da API
├── app/                       # Módulos Python compartilhados (ex: collections_mongo, collection_qdrant)
│   ├── init.py
│   ├── collection_qdrant.py
│   └── collections_mongo.py
├── data/                      # Arquivos JSON com dados brutos para população
│   ├── applicants.json
│   ├── prospects.json
│   └── vagas.json
├── insertion/                 # Scripts para população inicial de dados (MongoDB e Qdrant)
│   ├── Dockerfile             # Dockerfile para o populator (uso interno/Cloud Build)
│   ├── insertion_mongodb.py
│   ├── insertion_qdrant.py
│   └── requirements.txt       # Dependências do populator
├── models/                    # Modelos de ML pré-baixados (SentenceTransformer, TF-IDF)
│   ├── distiluse-base-multilingual-cased-v1/
│   └── tfidf_vectorizer.pkl
├── streamlit_app/             # Aplicação Streamlit para o frontend (UX)
│   ├── Dockerfile             # Dockerfile para o serviço Streamlit
│   ├── app.py                 # Ponto de entrada da aplicação Streamlit
│   └── requirements.txt       # Dependências do Streamlit
├── .secrets/                  # (Opcional, para desenvolvimento local seguro de tokens)
│   └── databricks_token.txt   # Contém o token Databricks (Adicionar ao .gitignore!)
└── docker-compose_TEST.yaml   # Configuração para deploy local com Docker Compose
```
## **Pré-requisitos**

Certifique-se de ter as seguintes ferramentas instaladas e configuradas:

* **Docker Desktop:** Para rodar contêineres e Docker Compose localmente.
* **Google Cloud SDK (`gcloud CLI`):** Para interagir com o Google Cloud e GKE.
* **`kubectl`:** Ferramenta de linha de comando do Kubernetes.
* **Helm:** Gerenciador de pacotes Kubernetes (usado para MongoDB e Qdrant no GKE).
* **`python`, `uv` e `pip`:** Para gerenciar dependências e executar scripts localmente.
* **Credenciais Google Cloud:** Uma conta GCP com créditos e permissões adequadas.
* **Token Databricks:** Para acesso aos modelos MLflow (se aplicável).

## **Deploy Local com Docker Compose**

Esta seção descreve como subir todos os serviços localmente usando Docker Compose.

1.  **Configure o Token Databricks (Apenas se a API precisar em runtime local):**
    * No seu `docker-compose_TEST.yaml`, a variável `DATABRICKS_TOKEN` que será usada pelo GKE com um secret

2.  **Verifique os Dockerfiles e `requirements.txt`:**
    * `api/Dockerfile`: Verifique se os caminhos `COPY` e o `CMD` estão corretos para a estrutura local.
    * `streamlit_app/Dockerfile`: Verifique os caminhos `COPY` e o `CMD`.
    * `api/requirements.txt`: Deve conter todas as dependências da API (incluindo as de `insertion/` se unificadas).
    * `streamlit_app/requirements.txt`: Deve conter dependências do Streamlit e cliente HTTP.

3.  **Inicie os Serviços:**
    * Abra o terminal na **raiz do seu projeto** (`seu_projeto_principal/`).
    * Execute o comando para construir as imagens e subir os serviços:
        ```bash
        docker compose -f docker-compose_TEST.yaml up --build -d
        ```
    * `--build`: Garante que as imagens são construídas a partir dos `Dockerfiles` (ou reconstruídas se houver mudanças).
    * `-d`: Roda os serviços em segundo plano.

4.  **Verifique o Status dos Serviços:**
    ```bash
    docker compose -f docker-compose_TEST.yaml ps
    docker compose -f docker-compose_TEST.yaml logs -f
    ```

5.  **Acesse os Serviços Localmente:**
    * **API:** `http://localhost:8000`
    * **Streamlit UX:** `http://localhost:8501`
    * **Mongo Express:** `http://localhost:8081` (interface web para MongoDB)

6.  **Parar Serviços Locais:**
    ```bash
    docker compose -f docker-compose_TEST.yaml down # Para e remove contêineres
    docker compose -f docker-compose_TEST.yaml down --volumes # Para, remove contêineres e volumes de dados (CUIDADO!)
    ```

## **Deploy na Nuvem com Google Kubernetes Engine (GKE)**

Esta seção descreve o processo para implantar a API e outros componentes no GKE.

### **Fase 1: Configuração do GKE e Bases de Dados**

1.  **Configure o Projeto Google Cloud:**
    ```bash
    gcloud config set project SEU_ID_DO_PROJETO
    gcloud services enable container.googleapis.com compute.googleapis.com artifactregistry.googleapis.com
    ```

2.  **Crie o Cluster GKE:**
    ```bash
    gcloud container clusters create meu-cluster-estudo \
        --zone southamerica-east1-b \
        --machine-type e2-small \
        --num-nodes 1 \
        --enable-autoscaling --min-nodes 1 --max-nodes 2 # Aumente max-nodes para mais recursos
        --enable-ip-alias
    ```

3.  **Obtenha Credenciais do Cluster:**
    ```bash
    gcloud container clusters get-credentials meu-cluster-estudo --zone southamerica-east1-b
    ```

4.  **Deploy do MongoDB no GKE (via Helm Bitnami):**
    * Adicione o repositório Bitnami:
        `helm repo add bitnami https://charts.bitnami.com/bitnami`
        `helm repo update`
    * Instale o MongoDB (substitua `SUA_SENHA_FORTE`):
        ```bash
        helm install meu-mongodb bitnami/mongodb \
            --version <VER_MAIS_RECENTE> \
            --set auth.rootPassword=SUA_SENHA_FORTE \
            --set persistence.size=8Gi \
            --set replicaSet.enabled=false \
            --set architecture=standalone \
            --set service.type=ClusterIP
        ```
    * Verifique: `kubectl get pods -l app.kubernetes.io/instance=meu-mongodb`

5.  **Deploy do Qdrant no GKE (via Helm):**
    * Adicione o repositório Qdrant:
        `helm repo add qdrant https://qdrant.github.io/qdrant-helm`
        `helm repo update`
    * Instale o Qdrant:
        ```bash
        helm install meu-qdrant qdrant/qdrant \
            --version <VER_MAIS_RECENTE> \
            --set persistence.enabled=true \
            --set persistence.size=8Gi
        ```
    * Verifique: `kubectl get pods -l app.kubernetes.io/name=qdrant`

### **Fase 2: Deploy da API no GKE**

1.  **Configure o `api/Dockerfile`:**
    * Use o `Dockerfile` completo fornecido nas discussões anteriores, que copia os modelos e as pastas `api/`, `app/`, `insertion/` e configura o Uvicorn corretamente.
    * Certifique-se de que `main.py`, `utils.py`, `requirements.txt` estão na pasta `api/`.
    * Certifique-se de que `models/` e `app/` estão na raiz do projeto.
    * Crie `.secrets/databricks_token.txt` na raiz do projeto com seu token. (Adicione `.secrets/` ao `.dockerignore`).

2.  **Construa e Envie a Imagem Docker da API:**
    * Abra o terminal na **raiz do seu projeto**.
    * Construa a imagem (usando `powershell` no Windows):
        ```powershell
        $env:DOCKER_BUILDKIT=1; docker build `
            --secret id=databricks_token,src=.secrets/databricks_token.txt `
            -t gcr.io/SEU_ID_DO_PROJETO/sua-api:latest `
            -f api/Dockerfile .
        ```
    * Envie para o GCR (pode levar tempo):
        ```powershell
        docker push gcr.io/SEU_ID_DO_PROJETO/sua-api:latest
        ```

3.  **Crie o Secret para o Token Databricks no GKE:**
    ```bash
    kubectl create secret generic databricks-api-token --from-literal=token=**************
    ```

4.  **Crie o Manifesto `api-deployment.yaml`:**
    * Use o manifesto `api-deployment.yaml` que as variáveis de ambiente para MongoDB, Qdrant e MLflow (com o token salvo ngo Secret).
    * **Substitua `SUA_SENHA_FORTE` pela senha real do MongoDB.**
    * **Ajuste `resources` (`requests` e `limits`)** se o Pod da API continuar falhando por falta de memória.

5.  **Aplique o Manifesto no GKE:**
    ```bash
    kubectl apply -f api-deployment.yaml
    ```

6.  **Obtenha o Endereço Público da API:**
    ```bash
    kubectl get svc minha-api-service --watch
    ```
    * Aguarde o `EXTERNAL-IP` aparecer.

### **Fase 3: População dos Bancos de Dados (Após o Deploy da API)**

Você pode popular os bancos de dados MongoDB e Qdrant usando Pods temporários no GKE, o que é mais eficiente para grandes volumes de dados.

1.  **Configure o `insertion/Dockerfile`:**
    * Use o `Dockerfile` para o populator fornecido anteriormente, que copia os scripts de inserção e os arquivos JSON de dados.
    * Certifique-se de que as strings de conexão nos scripts (`insertion_mongodb.py`, `app/collection_qdrant.py`) usam os nomes de serviço internos do GKE (`meu-mongodb`, `meu-qdrant`).

2.  **Construa e Envie a Imagem Docker do Populator (via Cloud Build para evitar carga local):**
    * Abra o terminal na **raiz do seu projeto**.
    * Envie o build para o Cloud Build:
        ```bash
        gcloud builds submit . --tag gcr.io/SEU_ID_DO_PROJETO/data-populator:latest --dockerfile insertion/Dockerfile
        ```
    * Monitore o link de logs na nuvem.

3.  **Execute os Scripts de População no GKE (como Pods temporários):**
    * Após a imagem `data-populator` estar no GCR:
        ```bash
        kubectl run mongo-populator --image=gcr.lo/SEU_ID_DO_PROJETO/data-populator:latest \
            --restart=Never --rm -it -- \
            python insertion_mongodb.py

        kubectl run qdrant-populator --image=gcr.lo/SEU_ID_DO_PROJETO/data-populator:latest \
            --restart=Never --rm -it -- \
            python insertion_qdrant.py
        ```

### **Fase 4: Deploy do Streamlit UX no GKE (Opcional, ou usar Streamlit Cloud)**

1.  **Configure o `streamlit_app/Dockerfile`:**
    * Use o `Dockerfile` para o Streamlit fornecido anteriormente.

2.  **Construa e Envie a Imagem Docker do Streamlit:**
    * Abra o terminal na **raiz do seu projeto**.
    * Construa a imagem:
        ```powershell
        docker build -t gcr.io/SEU_ID_DO_PROJETO/sua-streamlit-app:latest -f streamlit_app/Dockerfile .
        ```
    * Envie para o GCR:
        ```powershell
        docker push gcr.io/SEU_ID_DO_PROJETO/sua-streamlit-app:latest
        ```

3.  **Crie o Manifesto `streamlit-deployment.yaml`:**
    * Configure um `Deployment` similar ao da API, com `image`, `ports`, e `env` (API_BASE_URL apontando para o nome do serviço `minha-api-service` interno no GKE: `http://minha-api-service:80`).
    * Configure um `Service` do tipo `LoadBalancer` para o Streamlit (na porta 8501).

4.  **Aplique o Manifesto no GKE:**
    ```bash
    kubectl apply -f streamlit-deployment.yaml
    ```
5.  **Obtenha o Endereço Público do Streamlit:**
    ```bash
    kubectl get svc minha-streamlit-service --watch
    ```
## **Acesso à API Pública**
Acesse: http://34.151.203.159/

## **Video Explicativo no Youtube**

https://youtu.be/-q2fPxk_mrE

## **Limpeza de Recursos (Importante para Evitar Custos)**

Quando terminar seu projeto de estudo, **delete o cluster GKE** para parar de incorrer em custos.

```bash
gcloud container clusters delete meu-cluster-estudo --zone southamerica-east1-b
```

Você também pode remover as imagens do GCR/Artifact Registry se não precisar delas:
```
gcloud container images delete gcr.io/SEU_ID_DO_PROJETO/sua-api:latest
gcloud container images delete gcr.io/SEU_ID_DO_PROJETO/data-populator:latest
gcloud container images delete gcr.io/SEU_ID_DO_PROJETO/sua-streamlit-app:latest

```


