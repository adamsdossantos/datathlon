from fastapi import FastAPI
from app.matching_functions import vagas_match, applicants_match
from api.utils import MatchRequestJob, MatchRequestApplicant
from app.tf_idf_cache import start_background_refresh
from insertion.insertion_qdrand import start_qdrant_background_sync
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app:FastAPI):
   print("Lifespan: Starting background refresh for MongoDB...")
   start_background_refresh()
   print("MongoDB refreshed")
   print("Iniciando refresh do Qdrand")
   start_qdrant_background_sync()
   print("Qdrant refreshed")
   yield 


app = FastAPI(
    title="API de Match de Vagas e Candidatos",
    description="API para encontrar os melhores matches entre vagas e candidatos.",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "API de Match de Candidatos e Vagas"}


@app.post("/match/vagas", tags=["Matching"])
def match_vagas_endpoint(request: MatchRequestJob):
    """
    Recebe o ID de uma vaga e retorna os candidatos mais compatíveis.
    """
    return vagas_match(
        job_id=request.job_id, 
        top_n=request.top_n, 
        alpha=request.alpha
    )

@app.post("/match/applicants", tags=["Matching"])
def match_applicants_endpoint(request: MatchRequestApplicant):
    """
    Recebe o ID de um candidato e retorna as vagas mais compatíveis.
    """
    return applicants_match(
        applicant_id=request.applicant_id, 
        top_n=request.top_n, 
        alpha=request.alpha
    )

@app.get("/health", tags=["Health Check"])
def health_check():
    """
    Endpoint para verificar a saúde da aplicação.
    """
    return {"status": "ok"}
