#!/bin/bash
# Script para corrigir problemas do Cloud Build

echo "=== Correção do Cloud Build ==="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Nenhum projeto configurado${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Projeto: ${PROJECT_ID}${NC}"
echo ""

# Lista triggers existentes
echo -e "${YELLOW}📋 Verificando triggers existentes...${NC}"
TRIGGERS=$(gcloud builds triggers list --format="value(name)" 2>/dev/null)

if [ -n "$TRIGGERS" ]; then
    echo "Triggers encontrados:"
    echo "$TRIGGERS"
    echo ""
    
    read -p "Deseja deletar todos os triggers existentes? (s/n): " DELETE_TRIGGERS
    if [ "$DELETE_TRIGGERS" = "s" ]; then
        for trigger in $TRIGGERS; do
            echo "Deletando trigger: $trigger"
            gcloud builds triggers delete "$trigger" --quiet
        done
        echo -e "${GREEN}✅ Triggers deletados${NC}"
    fi
else
    echo "Nenhum trigger encontrado"
fi

echo ""
echo -e "${YELLOW}📋 Problema identificado: Cloud Build está tentando usar Docker${NC}"
echo "Seu projeto tem um Dockerfile em deploy/ mas está configurado para App Engine"
echo ""
echo "Escolha a solução:"
echo "1) Usar configuração App Engine (recomendada - sem Docker)"
echo "2) Usar configuração simples (mínima, apenas deploy)"
echo "3) Desabilitar Cloud Build (usar apenas deploy manual)"
read -p "Opção: " BUILD_OPTION

case $BUILD_OPTION in
    1)
        echo -e "${YELLOW}📦 Configurando Cloud Build para App Engine...${NC}"
        
        # Verifica se o repositório está conectado
        echo "Para criar o trigger, você precisa ter o repositório conectado ao Cloud Build."
        echo "Acesse: https://console.cloud.google.com/cloud-build/repos"
        echo ""
        read -p "O repositório já está conectado? (s/n): " REPO_CONNECTED
        
        if [ "$REPO_CONNECTED" = "s" ]; then
            read -p "Nome do repositório (ex: jfr1beiro/quzapp_v1.3): " REPO_NAME
            read -p "Branch para trigger (ex: main ou master): " BRANCH_NAME
            
            # Cria trigger usando a configuração App Engine
            gcloud builds triggers create github \
                --repo-name="$REPO_NAME" \
                --branch-pattern="^${BRANCH_NAME}$" \
                --build-config="cloudbuild-appengine.yaml" \
                --description="Deploy App Engine do Quiz App" \
                --name="quiz-app-appengine-deploy"
            
            echo -e "${GREEN}✅ Trigger App Engine criado!${NC}"
        else
            echo -e "${YELLOW}⚠️  Configure o repositório primeiro no console${NC}"
        fi
        ;;
    2)
        echo -e "${YELLOW}📦 Configurando Cloud Build simples...${NC}"
        
        read -p "O repositório já está conectado? (s/n): " REPO_CONNECTED
        
        if [ "$REPO_CONNECTED" = "s" ]; then
            read -p "Nome do repositório (ex: jfr1beiro/quzapp_v1.3): " REPO_NAME
            read -p "Branch para trigger (ex: main ou master): " BRANCH_NAME
            
            # Cria trigger usando a configuração simples
            gcloud builds triggers create github \
                --repo-name="$REPO_NAME" \
                --branch-pattern="^${BRANCH_NAME}$" \
                --build-config="cloudbuild-simple.yaml" \
                --description="Deploy simples do Quiz App" \
                --name="quiz-app-simple-deploy"
            
            echo -e "${GREEN}✅ Trigger simples criado!${NC}"
        else
            echo -e "${YELLOW}⚠️  Configure o repositório primeiro no console${NC}"
        fi
        ;;
    3)
        echo -e "${YELLOW}⚠️  Desabilitando Cloud Build automático...${NC}"
        echo "Use apenas deploy manual com: ./deploy.sh"
        ;;
esac

echo ""
echo -e "${YELLOW}🔧 Verificando configurações do App Engine...${NC}"

# Verifica se app.yaml está correto
if [ -f "app.yaml" ]; then
    echo -e "${GREEN}✅ app.yaml encontrado${NC}"
    
    # Verifica se não há referências a Docker
    if grep -q "dockerfile\|docker" app.yaml; then
        echo -e "${RED}❌ app.yaml contém referências a Docker${NC}"
        echo "App Engine não usa Docker. Removendo referências..."
        sed -i '/dockerfile/d' app.yaml
        sed -i '/docker/d' app.yaml
        echo -e "${GREEN}✅ Referências removidas${NC}"
    fi
else
    echo -e "${RED}❌ app.yaml não encontrado${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Correções aplicadas!${NC}"
echo ""
echo "Próximos passos:"
echo "1. Se criou um trigger, faça push do código para disparar o build"
echo "2. Se preferir deploy manual, use: ./deploy.sh"
echo "3. Para testar localmente: python app.py"
echo ""
echo "Para monitorar builds: https://console.cloud.google.com/cloud-build/builds"