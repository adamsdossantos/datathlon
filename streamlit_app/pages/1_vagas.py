import streamlit as st
import requests
import pandas as pd

st.set_page_config(
    page_title="Vagas App",
    layout="centered",
    initial_sidebar_state='expanded',
    menu_items={
        'About': "# This is a header. This is an *extremely* cool app!",
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        }       
)


st.title("Vagas")


job_id = st.text_input("Job ID")
top_n = st.number_input("Quantidade de Candidatos", min_value=1, max_value=20, value=5)

if st.button("Gerar Cadidatos"):
    payload = {"job_id": job_id, 
               "top_n": top_n
               }
    response = requests.post("http://localhost:8000/match/vagas", json=payload)

    if response.ok:
        data = response.json()
        for match in data:
            vaga = match['vaga']
            applicants = match['top_applicants']
            st.subheader(f"Vaga: {vaga['titulo_vaga']}")
            st.write(f"Empresa: {vaga['cliente']}")
            df=pd.DataFrame(applicants)
            df['score'] = df["score"].round(3)
            st.dataframe(df)
    else:
        st.error("Error:" + response.text)