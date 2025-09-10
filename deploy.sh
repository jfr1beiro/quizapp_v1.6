#!/bin/bash
# Script de deploy para Google App Engine

echo "=== Deploy do Quiz App para Google Cloud ==="
echo ""

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verifica se gcloud está instalado
if ! command -v gcloud &> /dev/null
then
    echo -e "${RED}❌ Google Cloud CLI não está instalado!${NC}"
    echo "Execute primeiro: ./gcloud_setup.sh"
    exit 1
fi

# Verifica se está autenticado
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Você não está autenticado no Google Cloud${NC}"
    echo "Execute: gcloud auth login"
    exit 1
fi

# Obtém o projeto atual
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Nenhum projeto configurado${NC}"
    echo "Execute: gcloud config set project SEU_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✅ Projeto configurado: ${PROJECT_ID}${NC}"
echo ""

# Opções de deploy
echo "Escolha o tipo de deploy:"
echo "1) Deploy completo (recomendado para primeira vez)"
echo "2) Deploy rápido (apenas código, sem dependências)"
echo "3) Deploy usando Secret Manager (recomendado para produção)"
echo "4) Deploy com promoção de tráfego gradual"
read -p "Opção: " DEPLOY_OPTION

case $DEPLOY_OPTION in
    1)
        echo -e "${YELLOW}📦 Fazendo deploy completo...${NC}"
        gcloud app deploy app.yaml --quiet
        ;;
    2)
        echo -e "${YELLOW}🚀 Fazendo deploy rápido...${NC}"
        gcloud app deploy app.yaml --quiet --no-cache
        ;;
    3)
        echo -e "${YELLOW}🔐 Deploy usando Secret Manager...${NC}"
        echo "Este modo usa os secrets já configurados no Google Secret Manager"
        echo "Se você não configurou os secrets, execute primeiro: ./setup_secrets.sh"
        echo ""
        
        # Obtém secrets e faz deploy
        SECRET_KEY=$(gcloud secrets versions access latest --secret="quiz-secret-key" 2>/dev/null)
        ADMIN_EMAIL=$(gcloud secrets versions access latest --secret="quiz-admin-email" 2>/dev/null)
        ADMIN_PASSWORD=$(gcloud secrets versions access latest --secret="quiz-admin-password" 2>/dev/null)
        GCS_BUCKET=$(gcloud secrets versions access latest --secret="quiz-gcs-bucket" 2>/dev/null)
        
        if [ -z "$SECRET_KEY" ]; then
            echo -e "${RED}❌ Secrets não encontrados. Execute ./setup_secrets.sh primeiro${NC}"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Secrets encontrados${NC}"
        gcloud app deploy app.yaml --quiet \
            --set-env-vars="SECRET_KEY=${SECRET_KEY},ADMIN_EMAIL=${ADMIN_EMAIL},ADMIN_DEFAULT_PASSWORD=${ADMIN_PASSWORD},GCS_BUCKET_NAME=${GCS_BUCKET}"
        ;;
    4)
        echo -e "${YELLOW}📈 Deploy com promoção gradual...${NC}"
        read -p "Porcentagem inicial de tráfego (ex: 10): " TRAFFIC_PCT
        gcloud app deploy app.yaml --quiet --no-promote
        
        VERSION=$(gcloud app versions list --service=default --format="value(version.id)" --limit=1)
        echo -e "${GREEN}✅ Versão ${VERSION} deployada sem tráfego${NC}"
        
        read -p "Promover versão com ${TRAFFIC_PCT}% do tráfego? (s/n): " CONFIRM
        if [ "$CONFIRM" = "s" ]; then
            gcloud app services set-traffic default --splits ${VERSION}=${TRAFFIC_PCT} --quiet
            echo -e "${GREEN}✅ Tráfego configurado: ${TRAFFIC_PCT}%${NC}"
        fi
        ;;
    *)
        echo -e "${RED}❌ Opção inválida${NC}"
        exit 1
        ;;
esac

# Verifica se o deploy foi bem-sucedido
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Deploy realizado com sucesso!${NC}"
    echo ""
    
    # Mostra a URL da aplicação
    APP_URL="https://${PROJECT_ID}.appspot.com"
    echo -e "🌐 Sua aplicação está disponível em: ${GREEN}${APP_URL}${NC}"
    echo ""
    
    # Opções pós-deploy
    echo "O que deseja fazer agora?"
    echo "1) Abrir aplicação no navegador"
    echo "2) Ver logs em tempo real"
    echo "3) Ver estatísticas de uso"
    echo "4) Sair"
    read -p "Opção: " POST_OPTION
    
    case $POST_OPTION in
        1)
            echo "Abrindo aplicação..."
            if command -v xdg-open &> /dev/null; then
                xdg-open $APP_URL
            elif command -v open &> /dev/null; then
                open $APP_URL
            else
                echo "Abra manualmente: $APP_URL"
            fi
            ;;
        2)
            echo "Mostrando logs (Ctrl+C para sair)..."
            gcloud app logs tail -s default
            ;;
        3)
            echo "Abrindo console do App Engine..."
            gcloud app open-console
            ;;
        4)
            echo "Saindo..."
            ;;
    esac
else
    echo ""
    echo -e "${RED}❌ Erro durante o deploy${NC}"
    echo "Verifique os logs com: gcloud app logs read"
    exit 1
fi
