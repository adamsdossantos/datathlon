import streamlit as st

st.set_page_config(
    page_title="Decision Candidatos-Vagas App",
    layout='centered',
    initial_sidebar_state='expanded',
    menu_items={
        'About': "# This is a header. This is an *extremely* cool app!",
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        }       
)

st.title("Match Candidato Vaga")

st.header("Como Funciona:")

st.markdown("O app de match de cadidatos e vagas funciona da seguinte forma:\n\n " \
"- o sistema vetoriza as informações do corpus de vagas e de candidatos do **Mongo**\n\n" \
"- o modelo **TD-IDF** é treinado com as informações\n\n" \
"- o mesmo corpus está inserido no **Qdrant** vector database\n\n" \
"- quando há o **input** de um ID, seja da vaga ou do candidato, o modelo faz uma **média ponderada** dos " \
"resultados do consine similarity do TD-IDF e do consine do Qdrant gerando o score final")

