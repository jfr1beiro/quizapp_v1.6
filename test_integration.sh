#!/bin/bash
# Script para testar a integração com Google Cloud

echo "=== Teste de Integração Google Cloud ==="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Contadores
TESTS_PASSED=0
TESTS_FAILED=0

# Função para executar teste
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "🧪 ${test_name}... "
    
    if eval "$test_command" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ PASSOU${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FALHOU${NC}"
        ((TESTS_FAILED++))
    fi
}

# Função para executar teste com output
run_test_with_output() {
    local test_name=$1
    local test_command=$2
    
    echo -e "${BLUE}🧪 ${test_name}${NC}"
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSOU${NC}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}❌ FALHOU${NC}"
        ((TESTS_FAILED++))
    fi
    echo ""
}

echo -e "${YELLOW}📋 Verificando configurações básicas...${NC}"
echo ""

# Testa gcloud CLI
run_test "Google Cloud CLI instalado" "command -v gcloud"

# Testa autenticação
run_test "Usuário autenticado" "gcloud auth list --filter=status:ACTIVE --format='value(account)' | grep -q ."

# Testa projeto configurado
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -n "$PROJECT_ID" ]; then
    echo -e "🧪 Projeto configurado... ${GREEN}✅ PASSOU${NC} (${PROJECT_ID})"
    ((TESTS_PASSED++))
else
    echo -e "🧪 Projeto configurado... ${RED}❌ FALHOU${NC}"
    ((TESTS_FAILED++))
fi

echo ""
echo -e "${YELLOW}📋 Verificando APIs habilitadas...${NC}"
echo ""

# Testa APIs
run_test "App Engine API" "gcloud services list --enabled --filter='name:appengine.googleapis.com' --format='value(name)' | grep -q appengine"
run_test "Secret Manager API" "gcloud services list --enabled --filter='name:secretmanager.googleapis.com' --format='value(name)' | grep -q secretmanager"
run_test "Cloud Storage API" "gcloud services list --enabled --filter='name:storage.googleapis.com' --format='value(name)' | grep -q storage"

echo ""
echo -e "${YELLOW}📋 Verificando secrets...${NC}"
echo ""

# Testa secrets
run_test "Secret quiz-secret-key existe" "gcloud secrets describe quiz-secret-key"
run_test "Secret quiz-admin-email existe" "gcloud secrets describe quiz-admin-email"
run_test "Secret quiz-admin-password existe" "gcloud secrets describe quiz-admin-password"
run_test "Secret quiz-gcs-bucket existe" "gcloud secrets describe quiz-gcs-bucket"

echo ""
echo -e "${YELLOW}📋 Verificando App Engine...${NC}"
echo ""

# Testa App Engine
run_test "App Engine app existe" "gcloud app describe"

echo ""
echo -e "${YELLOW}📋 Verificando arquivos de configuração...${NC}"
echo ""

# Testa arquivos
run_test "app.yaml existe" "test -f app.yaml"
run_test "cloudbuild.yaml existe" "test -f cloudbuild.yaml"
run_test "requirements.txt existe" "test -f requirements.txt"
run_test ".gcloudignore existe" "test -f .gcloudignore"

echo ""
echo -e "${YELLOW}📋 Verificando dependências Python...${NC}"
echo ""

# Testa imports Python
run_test_with_output "Testando imports Python" "python3 -c '
try:
    import flask
    print(f\"  ✅ Flask {flask.__version__}\")
    
    import bcrypt
    print(f\"  ✅ bcrypt disponível\")
    
    from google.cloud import secretmanager
    print(f\"  ✅ Secret Manager client disponível\")
    
    from google.cloud import storage
    print(f\"  ✅ Cloud Storage client disponível\")
    
    from google.cloud import logging
    print(f\"  ✅ Cloud Logging client disponível\")
    
    print(\"  ✅ Todas as dependências OK\")
except ImportError as e:
    print(f\"  ❌ Erro de import: {e}\")
    exit(1)
except Exception as e:
    print(f\"  ❌ Erro: {e}\")
    exit(1)
'"

# Testa bucket GCS se existir
if [ -n "$PROJECT_ID" ]; then
    echo -e "${YELLOW}📋 Verificando Google Cloud Storage...${NC}"
    echo ""
    
    BUCKET_NAME=$(gcloud secrets versions access latest --secret="quiz-gcs-bucket" 2>/dev/null)
    if [ -n "$BUCKET_NAME" ]; then
        run_test "Bucket GCS existe" "gsutil ls -b gs://${BUCKET_NAME}"
    else
        echo "🧪 Bucket GCS... ⚠️  Não configurado"
    fi
fi

echo ""
echo -e "${YELLOW}📋 Verificando permissões...${NC}"
echo ""

# Testa permissões
if [ -n "$PROJECT_ID" ]; then
    run_test "App Engine service account tem acesso ao Secret Manager" "gcloud projects get-iam-policy ${PROJECT_ID} --flatten='bindings[].members' --format='table(bindings.role)' --filter='bindings.members:${PROJECT_ID}@appspot.gserviceaccount.com AND bindings.role:roles/secretmanager.secretAccessor' | grep -q secretmanager"
fi

echo ""
echo "=== RESUMO DOS TESTES ==="
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 TODOS OS TESTES PASSARAM!${NC}"
    echo -e "${GREEN}✅ ${TESTS_PASSED}/${TOTAL_TESTS} testes bem-sucedidos${NC}"
    echo ""
    echo -e "${BLUE}🚀 Sua integração com Google Cloud está pronta!${NC}"
    echo ""
    echo "Próximos passos:"
    echo "1. Execute: ./deploy.sh (opção 3)"
    echo "2. Acesse: https://${PROJECT_ID}.appspot.com"
    echo "3. Configure monitoramento: ./monitoring_setup.sh"
else
    echo -e "${RED}❌ ALGUNS TESTES FALHARAM${NC}"
    echo -e "${RED}❌ ${TESTS_FAILED}/${TOTAL_TESTS} testes falharam${NC}"
    echo -e "${GREEN}✅ ${TESTS_PASSED}/${TOTAL_TESTS} testes bem-sucedidos${NC}"
    echo ""
    echo -e "${YELLOW}⚠️  Corrija os problemas antes de fazer deploy${NC}"
    echo ""
    echo "Comandos úteis:"
    echo "• Configurar projeto: ./gcloud_setup.sh"
    echo "• Configurar secrets: ./setup_secrets.sh"
    echo "• Ver documentação: cat GOOGLE_CLOUD_INTEGRATION.md"
fi

echo ""
echo -e "${BLUE}📚 Para mais informações, consulte:${NC}"
echo "• GOOGLE_CLOUD_INTEGRATION.md"
echo "• https://cloud.google.com/appengine/docs"