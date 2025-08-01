#!/bin/sh

# Inicia o servidor Ollama em segundo plano
ollama serve &

# Captura o ID do processo para poder aguardá-lo depois
pid=$!

echo "Servidor Ollama iniciado. Aguardando ficar online..."
# Aguarda um pouco para garantir que o servidor esteja pronto para receber comandos
sleep 5

echo "Puxando os modelos necessários a partir das variáveis de ambiente..."

# Puxa os modelos definidos nas variáveis de ambiente.
# Se a variável não for definida, ele não tentará baixar nada.
if [ -n "$EMBEDDING_MODEL" ]; then
  echo "Baixando modelo de embedding: $EMBEDDING_MODEL"
  ollama pull "$EMBEDDING_MODEL"
fi

if [ -n "$LLM_MODEL" ]; then
  echo "Baixando modelo de chat: $LLM_MODEL"
  ollama pull "$LLM_MODEL"
fi

echo "Modelos prontos."

# Aguarda o processo do servidor Ollama terminar
wait $pid
