#!/bin/bash
# Script para configurar Google Secret Manager

echo "=== Configuração do Google Secret Manager ==="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Obtém o projeto atual
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Nenhum projeto configurado${NC}"
    echo "Execute: gcloud config set project SEU_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✅ Projeto: ${PROJECT_ID}${NC}"
echo ""

# Habilita API do Secret Manager
echo -e "${YELLOW}📋 Habilitando Secret Manager API...${NC}"
gcloud services enable secretmanager.googleapis.com

# Função para criar secret
create_secret() {
    local secret_name=$1
    local secret_description=$2
    local secret_value=$3
    
    echo -e "${BLUE}🔐 Criando secret: ${secret_name}${NC}"
    
    # Verifica se o secret já existe
    if gcloud secrets describe $secret_name --quiet >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Secret ${secret_name} já existe. Criando nova versão...${NC}"
        echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
    else
        echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --replication-policy="automatic"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Secret ${secret_name} configurado${NC}"
    else
        echo -e "${RED}❌ Erro ao configurar ${secret_name}${NC}"
    fi
    echo ""
}

# Coleta informações sensíveis
echo -e "${YELLOW}📋 Configure as variáveis sensíveis do Quiz App:${NC}"
echo ""

# SECRET_KEY
echo "1. SECRET_KEY (chave secreta do Flask)"
echo "   Deixe vazio para gerar uma chave aleatória:"
read -p "SECRET_KEY: " SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    echo -e "${GREEN}✅ Chave gerada automaticamente${NC}"
fi

# ADMIN_EMAIL
echo ""
echo "2. ADMIN_EMAIL (email do administrador)"
read -p "ADMIN_EMAIL [j.f.s.r95@gmail.com]: " ADMIN_EMAIL
ADMIN_EMAIL=${ADMIN_EMAIL:-j.f.s.r95@gmail.com}

# ADMIN_PASSWORD
echo ""
echo "3. ADMIN_DEFAULT_PASSWORD (senha padrão do admin)"
read -s -p "ADMIN_DEFAULT_PASSWORD: " ADMIN_PASSWORD
echo ""

# GCS_BUCKET_NAME (opcional)
echo ""
echo "4. GCS_BUCKET_NAME (bucket para armazenamento - opcional)"
read -p "GCS_BUCKET_NAME [${PROJECT_ID}-quiz-storage]: " GCS_BUCKET_NAME
GCS_BUCKET_NAME=${GCS_BUCKET_NAME:-${PROJECT_ID}-quiz-storage}

echo ""
echo -e "${YELLOW}📋 Criando secrets...${NC}"
echo ""

# Cria os secrets
create_secret "quiz-secret-key" "Chave secreta do Flask" "$SECRET_KEY"
create_secret "quiz-admin-email" "Email do administrador" "$ADMIN_EMAIL"
create_secret "quiz-admin-password" "Senha padrão do administrador" "$ADMIN_PASSWORD"
create_secret "quiz-gcs-bucket" "Nome do bucket GCS" "$GCS_BUCKET_NAME"

# Cria bucket GCS se não existir
echo -e "${YELLOW}📦 Configurando Google Cloud Storage...${NC}"
if ! gsutil ls -b gs://$GCS_BUCKET_NAME >/dev/null 2>&1; then
    echo "Criando bucket: $GCS_BUCKET_NAME"
    gsutil mb gs://$GCS_BUCKET_NAME
    
    # Configura CORS para o bucket (se necessário)
    echo '[{"origin": ["*"], "method": ["GET", "POST", "PUT", "DELETE"], "responseHeader": ["Content-Type"], "maxAgeSeconds": 3600}]' > cors.json
    gsutil cors set cors.json gs://$GCS_BUCKET_NAME
    rm cors.json
    
    echo -e "${GREEN}✅ Bucket criado e configurado${NC}"
else
    echo -e "${GREEN}✅ Bucket já existe${NC}"
fi

echo ""

# Configura permissões para App Engine
echo -e "${YELLOW}📋 Configurando permissões...${NC}"
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

echo ""
echo -e "${GREEN}✅ Secret Manager configurado com sucesso!${NC}"
echo ""
echo -e "${BLUE}📋 Resumo dos secrets criados:${NC}"
echo "• quiz-secret-key"
echo "• quiz-admin-email" 
echo "• quiz-admin-password"
echo "• quiz-gcs-bucket"
echo ""
echo -e "${YELLOW}⚠️  Importante:${NC}"
echo "• Os secrets são acessíveis apenas pelo App Engine do seu projeto"
echo "• Você pode visualizar os secrets (mas não os valores) em:"
echo "  https://console.cloud.google.com/security/secret-manager"
echo ""
echo "Próximo passo: Execute ./deploy.sh para fazer o deploy"