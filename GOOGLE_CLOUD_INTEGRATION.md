# Guia de Integração com Google Cloud

Este guia explica como integrar completamente sua aplicação Quiz App com o Google Cloud Platform.

## 📋 Pré-requisitos

1. **Conta Google Cloud**: Crie uma conta em [cloud.google.com](https://cloud.google.com)
2. **Projeto Google Cloud**: Crie um novo projeto
3. **Billing habilitado**: Configure o faturamento no projeto
4. **Google Cloud SDK**: Instale o SDK localmente

## 🚀 Passos de Integração

### 1. Configuração Inicial

```bash
# 1. Executar setup inicial do Google Cloud
./gcloud_setup.sh

# 2. Configurar secrets (variáveis sensíveis)
./setup_secrets.sh

# 3. Configurar monitoramento (opcional)
./monitoring_setup.sh
```

### 2. Deploy da Aplicação

```bash
# Deploy usando Secret Manager (recomendado)
./deploy.sh
# Escolha a opção 3: "Deploy usando Secret Manager"
```

### 3. Configuração de CI/CD (Opcional)

```bash
# Configurar Cloud Build para deploy automático
./setup_cloud_build.sh
```

## 🔧 Recursos Integrados

### Google Secret Manager
- **SECRET_KEY**: Chave secreta do Flask
- **ADMIN_EMAIL**: Email do administrador
- **ADMIN_DEFAULT_PASSWORD**: Senha padrão do admin
- **GCS_BUCKET_NAME**: Nome do bucket para armazenamento

### Google Cloud Storage
- Armazenamento opcional para arquivos JSON
- Backup automático dos dados
- Configuração CORS para uploads

### Google Cloud Logging
- Logs centralizados da aplicação
- Monitoramento de erros em tempo real
- Métricas personalizadas

### Google App Engine
- Hospedagem serverless
- Escalonamento automático
- Health checks configurados

## 📊 Monitoramento

### Dashboards Disponíveis
- **Requests por minuto**: Tráfego da aplicação
- **Latência média**: Tempo de resposta
- **Taxa de erro**: Erros HTTP

### Alertas Configurados
- **Alta taxa de erro**: > 5% por 5 minutos
- **Alta latência**: > 2 segundos por 5 minutos
- **Notificações por email**

## 🔐 Segurança

### Práticas Implementadas
- Secrets gerenciados pelo Secret Manager
- HTTPS obrigatório
- Headers de segurança configurados
- Autenticação robusta para admin

### Permissões IAM
- App Engine Service Account com acesso mínimo necessário
- Cloud Build Service Account para deploy
- Secret Manager access para runtime

## 💰 Otimização de Custos

### Configurações de Economia
- **Instance Class F1**: Menor custo
- **Min instances: 0**: Não paga quando inativo
- **Max instances: 5**: Limita custos de escalonamento
- **Caching estático**: 7 dias para recursos estáticos

### Monitoramento de Custos
- Configure alertas de billing
- Monitore uso no console
- Revise métricas regularmente

## 🛠️ Comandos Úteis

### Logs
```bash
# Ver logs em tempo real
gcloud app logs tail -s default

# Ver logs específicos
gcloud app logs read --limit=50
```

### Versões
```bash
# Listar versões
gcloud app versions list

# Promover versão específica
gcloud app versions migrate VERSION_ID
```

### Secrets
```bash
# Listar secrets
gcloud secrets list

# Ver valor de um secret
gcloud secrets versions access latest --secret="quiz-secret-key"

# Atualizar secret
echo "novo_valor" | gcloud secrets versions add SECRET_NAME --data-file=-
```

### Storage
```bash
# Listar buckets
gsutil ls

# Ver conteúdo do bucket
gsutil ls gs://BUCKET_NAME

# Fazer backup manual
gsutil cp data/*.json gs://BUCKET_NAME/backup/
```

## 🔧 Troubleshooting

### Problemas Comuns

**1. Deploy falha com erro de permissão**
```bash
# Verificar permissões
gcloud projects get-iam-policy PROJECT_ID

# Reconfigurar permissões
./setup_cloud_build.sh
```

**2. Secrets não encontrados**
```bash
# Verificar se secrets existem
gcloud secrets list

# Recriar secrets
./setup_secrets.sh
```

**3. Aplicação não inicia**
```bash
# Verificar logs de erro
gcloud app logs read --severity=ERROR

# Verificar health check
curl https://PROJECT_ID.appspot.com/health
```

**4. Alta latência**
- Verificar instance class no app.yaml
- Otimizar queries do banco de dados
- Implementar cache se necessário

### Logs Importantes
- **Error Reporting**: Console > Error Reporting
- **Cloud Logging**: Console > Logging
- **App Engine Logs**: Console > App Engine > Versions

## 📱 URLs Importantes

Após o deploy, sua aplicação estará disponível em:
- **Aplicação**: `https://PROJECT_ID.appspot.com`
- **Admin**: `https://PROJECT_ID.appspot.com/admin`
- **Health Check**: `https://PROJECT_ID.appspot.com/health`

## 🔄 Atualizações

### Deploy de Atualizações
```bash
# Deploy simples
./deploy.sh
# Escolha opção 2: "Deploy rápido"

# Deploy com nova versão sem promover
gcloud app deploy --no-promote
```

### Rollback
```bash
# Voltar para versão anterior
gcloud app versions list
gcloud app services set-traffic default --splits=VERSION_ANTERIOR=100
```

## 📞 Suporte

Para problemas específicos:
1. Consulte os logs no Google Cloud Console
2. Verifique a documentação do App Engine
3. Use o Stack Overflow com tags: google-app-engine, python, flask

## 🎯 Próximos Passos

1. **Configure alertas de billing**
2. **Implemente backup automático**
3. **Configure SSL customizado (se necessário)**
4. **Otimize performance baseado em métricas**
5. **Configure domínio personalizado**