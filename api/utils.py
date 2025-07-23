from pydantic import BaseModel

class MatchRequestJob(BaseModel):
    job_id: str
    alpha: float = 0.3
    top_n: int = 5

class MatchRequestApplicant(BaseModel):
    applicant_id: str
    alpha: float = 0.3
    top_n: int = 5
