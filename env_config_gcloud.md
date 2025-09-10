# Configuração de Variáveis de Ambiente no Google Cloud

## Variáveis Obrigatórias

As seguintes variáveis de ambiente devem ser configuradas no Google Cloud Console:

### 1. SECRET_KEY
- **Descrição**: Chave secreta para sessões Flask
- **Valor Recomendado**: String aleatória de 32+ caracteres
- **Exemplo**: `sua_chave_secreta_super_segura_123456`

### 2. ADMIN_EMAIL
- **Descrição**: Email do administrador do sistema
- **Valor Atual**: `j.f.s.r95@gmail.com`

### 3. ADMIN_DEFAULT_PASSWORD
- **Descrição**: Senha padrão do administrador (primeiro acesso)
- **Valor Atual**: `Samu@220107`

## Como Configurar no Google Cloud Console

### Método 1: Via Console Web

1. Acesse o [Google Cloud Console](https://console.cloud.google.com)
2. Selecione seu projeto
3. Navegue para: **App Engine > Settings > Environment Variables**
4. Adicione cada variável com seu respectivo valor
5. Clique em **Save**

### Método 2: Via Command Line

```bash
# Configure as variáveis de ambiente
gcloud app deploy --set-env-vars="SECRET_KEY=sua_chave_secreta,ADMIN_EMAIL=j.f.s.r95@gmail.com,ADMIN_DEFAULT_PASSWORD=Samu@220107"
```

### Método 3: Via Secret Manager (Recomendado para produção)

```bash
# Criar secrets
echo -n "sua_chave_secreta_super_segura_123456" | gcloud secrets create secret-key --data-file=-
echo -n "j.f.s.r95@gmail.com" | gcloud secrets create admin-email --data-file=-
echo -n "Samu@220107" | gcloud secrets create admin-password --data-file=-

# Dar permissão ao App Engine
gcloud secrets add-iam-policy-binding secret-key \
    --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding admin-email \
    --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding admin-password \
    --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

## Variáveis Opcionais

### FLASK_ENV
- **Descrição**: Ambiente Flask
- **Valor**: `production` (já configurado no app.yaml)

### PERGUNTAS_JSON_PATH
- **Descrição**: Caminho para o arquivo de perguntas
- **Valor Padrão**: `data/perguntas.json`

## Notas Importantes

1. **Segurança**: Nunca commite valores reais de variáveis sensíveis no código
2. **Backup**: Mantenha um backup seguro dos valores das variáveis
3. **Rotação**: Considere rotacionar a SECRET_KEY periodicamente
4. **Senha Admin**: Altere a senha padrão após o primeiro login
