#!/bin/sh

# Inicia o servidor Ollama em segundo plano
ollama serve &

# Captura o ID do processo para poder aguardá-lo depois
pid=$!

echo "Servidor Ollama iniciado. Aguardando ficar online..."
# Aguarda um pouco para garantir que o servidor esteja pronto para receber comandos
sleep 5

echo "Puxando os modelos necessários (isso pode levar alguns minutos)..."

# Puxa os modelos. O Ollama os baixará se não existirem no volume.
# Se você mudar os modelos no docker-compose.yml, precisará adicioná-los aqui também.
ollama pull nomic-embed-text
ollama pull llama3

echo "Modelos prontos."

# Aguarda o processo do servidor Ollama terminar (o que nunca acontecerá, mantendo o contêiner ativo)
wait $pid
