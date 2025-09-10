#!/bin/bash
# Script para configurar Google Cloud CLI

echo "=== Configuração do Google Cloud CLI ==="
echo ""
echo "Este script ajudará você a configurar o Google Cloud CLI para deploy do Quiz App"
echo ""

# Verifica se o gcloud está instalado
if ! command -v gcloud &> /dev/null
then
    echo "❌ Google Cloud CLI não está instalado!"
    echo ""
    echo "Para instalar, visite: https://cloud.google.com/sdk/docs/install"
    echo ""
    echo "Ou execute:"
    echo "curl https://sdk.cloud.google.com | bash"
    exit 1
fi

echo "✅ Google Cloud CLI está instalado"
echo ""

# Inicia autenticação
echo "📋 Iniciando autenticação..."
gcloud auth login

# Configuração do projeto
echo ""
echo "📋 Configurando projeto..."
echo "Digite o ID do seu projeto Google Cloud:"
read PROJECT_ID

gcloud config set project $PROJECT_ID

# Habilita APIs necessárias
echo ""
echo "📋 Habilitando APIs necessárias..."
gcloud services enable appengine.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable cloudbuild.googleapis.com

# Cria app no App Engine
echo ""
echo "📋 Criando aplicação no App Engine..."
echo "Escolha a região (ex: us-central1, southamerica-east1):"
read REGION

gcloud app create --region=$REGION

echo ""
echo "✅ Configuração concluída!"
echo ""
echo "Projeto configurado: $PROJECT_ID"
echo "Região: $REGION"
echo ""
echo "Próximos passos:"
echo "1. Execute: ./deploy.sh para fazer o deploy"
echo "2. Configure as variáveis de ambiente no Console do Google Cloud"
