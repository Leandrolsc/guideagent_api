import streamlit as st
import requests
import os

# --- Configuration ---
# Get the API URL from environment variables, with a fallback for local development
API_URL = os.getenv("API_URL", "http://localhost:8000")
UPLOAD_ENDPOINT = f"{API_URL}/upload"
ADD_TEXT_ENDPOINT = f"{API_URL}/add_text"
CHAT_ENDPOINT = f"{API_URL}/chat"

# --- Streamlit Page Configuration ---
st.set_page_config(
    page_title="RAG Platform",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Plataforma RAG - Converse com seus Dados")
st.markdown("Faça upload de documentos (PDF, DOCX, MD) ou adicione texto e faça perguntas sobre o conteúdo.")

# --- Sidebar for Data Input ---
with st.sidebar:
    st.header("Adicionar Conhecimento")

    # Option to choose between file upload and text input
    input_method = st.radio(
        "Escolha o método de entrada:",
        ("Upload de Arquivo", "Inserir Texto")
    )

    if input_method == "Upload de Arquivo":
        uploaded_file = st.file_uploader(
            "Escolha um arquivo (PDF, DOCX, MD)",
            type=['pdf', 'docx', 'md']
        )
        if st.button("Processar Arquivo"):
            if uploaded_file is not None:
                with st.spinner('Processando e vetorizando o arquivo...'):
                    files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    try:
                        response = requests.post(UPLOAD_ENDPOINT, files=files, timeout=300)
                        if response.status_code == 200:
                            st.success('Arquivo processado com sucesso!')
                        else:
                            st.error(f"Erro ao processar o arquivo: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Erro de conexão com a API: {e}")
            else:
                st.warning("Por favor, faça o upload de um arquivo primeiro.")

    elif input_method == "Inserir Texto":
        raw_text = st.text_area("Cole o texto aqui:", height=200)
        if st.button("Processar Texto"):
            if raw_text:
                with st.spinner('Processando e vetorizando o texto...'):
                    try:
                        payload = {"text": raw_text}
                        response = requests.post(ADD_TEXT_ENDPOINT, json=payload, timeout=120)
                        if response.status_code == 200:
                            st.success('Texto processado com sucesso!')
                        else:
                            st.error(f"Erro ao processar o texto: {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Erro de conexão com a API: {e}")
            else:
                st.warning("Por favor, insira um texto para processar.")

# --- Main Chat Interface ---
st.header("Chat")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Qual é a sua pergunta?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                payload = {"text": prompt}
                response = requests.post(CHAT_ENDPOINT, json=payload, timeout=300)
                if response.status_code == 200:
                    response_data = response.json()
                    full_response = response_data.get("response", "Não foi possível obter uma resposta.")
                    st.markdown(full_response)
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error(f"Erro na API: {response.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Erro de conexão com a API: {e}")
