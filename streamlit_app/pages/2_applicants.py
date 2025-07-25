import streamlit as st
import requests
import pandas as pd
import os

st.title("Candidatos")

applicant_id = st.text_input("Candidato ID")
top_n = st.number_input("Quantidade de Vagas", min_value=1, max_value=20, value=5)

if st.button("Gerar Vagas"):
    payload = {"applicant_id": applicant_id, 
               "top_n": top_n
               }
    api_url = os.getenv("API_URL", "http://localhost:8000")  # fallback para desenvolvimento local
    response = requests.post(f"{api_url}/match/applicants", json=payload)

    response = requests.post("http://api:8000/match/applicants", json=payload)

    if response.ok:
        data = response.json()
        for match in data:
            applicant = match['applicant']
            vagas = match['top_vagas']
            st.subheader(f"Vaga: {applicant['nome']}")
            st.write(f"e-mail: {applicant['email']}")
            df=pd.DataFrame(vagas)
            df['score'] = df["score"].round(3)
            st.dataframe(df)
    else:
        st.error("Error:" + response.text)