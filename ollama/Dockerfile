# Usar a imagem oficial do Ollama como base
FROM ollama/ollama

# Copiar o script de entrypoint para dentro do contêiner
COPY entrypoint.sh /entrypoint.sh

# Dar permissão de execução ao script
RUN chmod +x /entrypoint.sh

# Definir o script como o ponto de entrada do contêiner
ENTRYPOINT ["/entrypoint.sh"]
