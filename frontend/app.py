import streamlit as st
import requests
import os
import json

# --- Configuration ---
API_URL = os.getenv("API_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{API_URL}/upload"
CHAT_ENDPOINT = f"{API_URL}/chat"

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="RAG Platform",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Plataforma RAG com Metadados Estruturados")
st.markdown("Faça upload de documentos com título, link e palavras-chave para melhorar a busca.")

# --- Sidebar for Data Input ---
with st.sidebar:
    st.header("Adicionar Conhecimento")

    uploaded_file = st.file_uploader(
        "Escolha um arquivo (PDF, DOCX, MD)",
        type=['pdf', 'docx', 'md']
    )
    
    # Novos campos para metadados estruturados
    title_input = st.text_input("Nome / Título do Arquivo *", help="O título principal do documento.")
    link_input = st.text_input("Link do Arquivo (Opcional)", help="URL para o documento original.")
    keywords_input = st.text_input(
        "Palavras-chave (separadas por ponto e vírgula)",
        help="Ex: relatório; finanças; Q3; 2024"
    )

    if st.button("Processar Arquivo"):
        if uploaded_file is not None and title_input:
            with st.spinner('Processando arquivo e metadados...'):
                files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                
                # CORREÇÃO: Divide a string de palavras-chave usando ';'
                keywords_list = [keyword.strip() for keyword in keywords_input.split(';') if keyword.strip()]
                
                # Prepara os dados do formulário com os novos campos
                form_data = {
                    'title': title_input,
                    'link': link_input,
                    'keywords': json.dumps(keywords_list)
                }

                try:
                    response = requests.post(UPLOAD_ENDPOINT, files=files, data=form_data, timeout=300)
                    if response.status_code == 200:
                        st.success('Arquivo e metadados processados com sucesso!')
                    else:
                        st.error(f"Erro ao processar: {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Erro de conexão com a API: {e}")
        else:
            st.warning("Por favor, faça o upload de um arquivo e preencha o título.")

# --- Main Chat Interface ---
st.header("Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

if prompt := st.chat_input("Qual é a sua pergunta?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                payload = {"text": prompt}
                response = requests.post(CHAT_ENDPOINT, json=payload, timeout=300)
                if response.status_code == 200:
                    response_data = response.json()
                    full_response = response_data.get("response", "Não foi possível obter uma resposta.")
                    sources = response_data.get("sources", [])
                    
                    st.markdown(full_response)
                    
                    # Exibe as fontes de forma estruturada com links
                    if sources:
                        st.markdown("---")
                        st.subheader("Fontes Consultadas:")
                        sources_html = ""
                        for source in sources:
                            title = source.get('title', source.get('filename'))
                            link = source.get('link')
                            if link:
                                sources_html += f"<li><a href='{link}' target='_blank'>{title}</a></li>"
                            else:
                                sources_html += f"<li>{title}</li>"
                        st.markdown(f"<ul>{sources_html}</ul>", unsafe_allow_html=True)
                    
                    # Adiciona a resposta completa ao histórico
                    response_with_sources = full_response
                    if sources:
                        response_with_sources += "\n\n---\n**Fontes:**"
                        for source in sources:
                             response_with_sources += f"\n- {source.get('title')}"
                    st.session_state.messages.append({"role": "assistant", "content": response_with_sources})
                else:
                    st.error(f"Erro na API: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão com a API: {e}")
