#!/bin/sh

ollama serve &

pid=$!

echo "Servidor Ollama iniciado. Aguardando ficar online..."
sleep 5

echo "Puxando os modelos necessários a partir das variáveis de ambiente..."

if [ -n "$EMBEDDING_MODEL" ]; then
  echo "Baixando modelo de embedding: $EMBEDDING_MODEL"
  ollama pull "$EMBEDDING_MODEL"
fi

if [ -n "$LLM_MODEL" ]; then
  echo "Baixando modelo de chat: $LLM_MODEL"
  ollama pull "$LLM_MODEL"
fi

echo "Modelos prontos."

wait $pid
