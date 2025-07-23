import streamlit as st
import requests
import pandas as pd

st.title("Candidatos")

applicant_id = st.text_input("Candidato ID")
top_n = st.number_input("Quantidade de Vagas", min_value=1, max_value=20, value=5)

if st.button("Gerar Vagas"):
    payload = {"applicant_id": applicant_id, 
               "top_n": top_n
               }
    response = requests.post("http://localhost:8000/match/applicants", json=payload)

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