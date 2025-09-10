# 🔧 Correção do Erro do Cloud Build

## ❌ Problema Identificado

O Cloud Build está tentando usar **Docker** em vez do **App Engine**. O erro ocorre porque:

1. Existe um `Dockerfile` na pasta `deploy/` 
2. O trigger do Cloud Build foi configurado incorretamente
3. O sistema está confundindo App Engine com Container/Docker

## ✅ Solução Rápida

### Opção 1: Script Automático (Recomendado)
```bash
./fix_cloudbuild.sh
# Escolha a opção 1: "Usar configuração App Engine"
```

### Opção 2: Correção Manual

1. **Deletar triggers existentes:**
```bash
# Listar triggers
gcloud builds triggers list

# Deletar trigger problemático
gcloud builds triggers delete TRIGGER_NAME
```

2. **Criar novo trigger correto:**
```bash
gcloud builds triggers create github \
    --repo-name="jfr1beiro/quzapp_v1.3" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild-appengine.yaml" \
    --description="Deploy App Engine do Quiz App" \
    --name="quiz-app-appengine-deploy"
```

### Opção 3: Deploy Manual (Mais Simples)
```bash
# Desabilitar Cloud Build e usar deploy manual
./deploy.sh
# Escolha a opção 3: "Deploy usando Secret Manager"
```

## 📋 Arquivos de Configuração Disponíveis

1. **`cloudbuild-appengine.yaml`** - Configuração completa para App Engine
2. **`cloudbuild-simple.yaml`** - Configuração mínima 
3. **`cloudbuild.yaml`** - Configuração original (pode ter conflitos)

## 🔍 Verificação

Após aplicar a correção, verifique:

```bash
# 1. Listar triggers
gcloud builds triggers list

# 2. Testar trigger manualmente
gcloud builds triggers run TRIGGER_NAME --branch=main

# 3. Monitorar build
gcloud builds list --limit=5
```

## ⚡ Solução Imediata

Se você precisa fazer deploy agora:

```bash
# Deploy direto sem Cloud Build
gcloud app deploy app.yaml --quiet
```

## 📞 Status do Erro

O erro `unable to prepare context: unable to evaluate symlinks in Dockerfile path` indica que o Cloud Build está procurando um Dockerfile na raiz do projeto, mas sua aplicação usa App Engine (que não precisa de Docker).

**Solução**: Use as configurações específicas para App Engine que criei acima.