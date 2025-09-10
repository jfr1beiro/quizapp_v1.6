#!/bin/bash
# Script para configurar Cloud Build e triggers

echo "=== Configuração do Cloud Build ==="
echo ""

# Cores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)

echo -e "${YELLOW}📋 Habilitando Cloud Build API...${NC}"
gcloud services enable cloudbuild.googleapis.com

echo ""
echo -e "${YELLOW}📋 Configurando permissões do Cloud Build...${NC}"
# Dá permissão ao Cloud Build para fazer deploy no App Engine
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}@cloudbuild.gserviceaccount.com" \
    --role="roles/appengine.appAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}@cloudbuild.gserviceaccount.com" \
    --role="roles/appengine.serviceAdmin"

# Permissão para acessar Secret Manager
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${PROJECT_ID}@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

echo ""
echo -e "${YELLOW}📋 Criando trigger do Cloud Build...${NC}"
echo "Conecte seu repositório GitHub/GitLab/Bitbucket primeiro no Console"
echo ""
echo "Deseja criar um trigger agora? (s/n)"
read -p "Resposta: " CREATE_TRIGGER

if [ "$CREATE_TRIGGER" = "s" ]; then
    read -p "Nome do repositório (ex: usuario/repo): " REPO_NAME
    read -p "Branch para trigger (ex: main): " BRANCH_NAME
    
    gcloud builds triggers create github \
        --repo-name="${REPO_NAME}" \
        --branch-pattern="^${BRANCH_NAME}$" \
        --build-config="cloudbuild.yaml" \
        --description="Deploy automático do Quiz App" \
        --name="quiz-app-deploy"
    
    echo -e "${GREEN}✅ Trigger criado com sucesso!${NC}"
fi

echo ""
echo -e "${GREEN}✅ Cloud Build configurado!${NC}"
echo ""
echo "Próximos passos:"
echo "1. Conecte seu repositório no Console do Cloud Build"
echo "2. Faça push do código para o branch configurado"
echo "3. O deploy será feito automaticamente"
