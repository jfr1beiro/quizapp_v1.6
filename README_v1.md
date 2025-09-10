# 🚀 Quiz Cloud - Sistema de Quiz para Enfermagem

Este projeto é uma evolução do sistema original "Quiz Interativo". Ele foi preparado para manutenção, atualização e deploy em nuvem (Google Cloud), sem afetar o projeto anterior.

---

## 🛠️ Manutenção e Atualização

### 1. **Editar Perguntas**
- Os arquivos de perguntas ficam em `data/perguntas.json` (quiz comum) e `data/perguntas_recuperacao_organizado.json` (recuperação ESF).
- Para editar, use um editor de texto ou a interface admin (`/admin`).
- Sempre faça backup antes de grandes alterações.

#### 1.1 Fluxo de sincronização (staging → principal)
- Prepare novas perguntas em um arquivo de staging (ex.: `perguntas_staging.json` ou `perguntas_test.json`).
- Use `sincronizar_perguntas.py` para mesclar no banco principal com backup e deduplicação. Por padrão, o script detecta o banco principal por `PERGUNTAS_JSON_PATH` (ou `data/perguntas.json`).

Comandos:
```bash
# Dry-run (apenas relata o que seria feito)
python sincronizar_perguntas.py --staging perguntas_test.json --dry-run

# Sincroniza usando PERGUNTAS_JSON_PATH (ou data/perguntas.json se não definido)
python sincronizar_perguntas.py --staging perguntas_test.json

# Apontar explicitamente o banco principal (ex.: versão anterior)
python sincronizar_perguntas.py --staging perguntas_test.json --main "G:/Meu Drive/prjetos python/quiz/quiz_1/data/perguntas.json"

# Desabilitar espelho local em data/perguntas.json
python sincronizar_perguntas.py --staging perguntas_test.json --no-mirror-local
```

Formato aceito no staging:
- Lista de perguntas `[...]` ou objeto `{ "perguntas": [ ... ] }`.

#### 1.2 Sistema de Perguntas do Professor

O sistema agora suporta **perguntas específicas do professor** com destaque visual e distribuição automática 70/30.

##### **Características das Perguntas do Professor:**
- ✅ **Destaque visual**: `👨‍🏫 **[PROFESSOR]**` no enunciado
- ✅ **Badge verde** na interface com legenda "📚 Material extraído de aula presencial"
- ✅ **Distribuição inteligente**: 70% perguntas do professor, 30% material oficial
- ✅ **Campos específicos**: `fonte_material`, `legenda`, `prioridade_selecao`

##### **Formato das Perguntas do Professor:**
```json
{
  "pergunta": "👨‍🏫 **[PROFESSOR]** Segundo explicado em aula sobre...",
  "opcoes": [
    "Opção correta detalhada",
    "Distrator plausível relacionado",
    "Distrator com erro conceitual comum",
    "Distrator com inversão lógica"
  ],
  "resposta_correta": "Opção correta detalhada",
  "categoria": "Tópico - Subtópico",
  "periodo": 2,
  "disciplina": "MORFOFISIOLOGIA II",
  "dificuldade": "medio",
  "explicacao": "Baseado nos apontamentos do professor: [explicação detalhada com fundamentação científica]",
  "referencia": "Apontamentos Prof. - [Tópico]",
  "fonte_material": "professor",
  "legenda": "📚 Material extraído de aula presencial",
  "prioridade_selecao": 0.7
}
```

##### **Script Base para Criação de Perguntas do Professor:**

**SEMPRE USE ESTE TEMPLATE** ao criar novas perguntas baseadas em material do professor:

```
PARÂMETROS DE GERAÇÃO:
✅ Disciplina: [NOME_DA_DISCIPLINA]
✅ Período: [1 ou 2]
✅ Dificuldade: MÉDIO e DIFÍCIL (sem perguntas fáceis)
✅ Formato: Múltipla escolha (4 alternativas)
✅ Categoria: Por tópicos específicos
✅ Explicação: Sempre detalhada e educativa

FOCOS PARA PERGUNTAS MÉDIO/DIFÍCIL:
MÉDIO:
- Aplicação de conceitos em situações clínicas
- Correlação entre estrutura e função
- Comparação entre diferentes sistemas
- Análise de mecanismos específicos

DIFÍCIL:
- Integração de múltiplos sistemas
- Análise de casos patológicos
- Correlações bioquímicas complexas
- Aplicações em diagnóstico/tratamento

TEMPLATE DE PERGUNTA:
{
  "pergunta": "👨‍🏫 **[PROFESSOR]** [Situação clínica/conceitual complexa baseada nos apontamentos]",
  "opcoes": [
    "Alternativa correta com detalhamento",
    "Distrator plausível relacionado",
    "Distrator com erro conceitual comum",
    "Distrator com inversão lógica"
  ],
  "resposta_correta": "[Resposta precisa]",
  "categoria": "[Tópico] - [Subtópico]",
  "periodo": [1 ou 2],
  "disciplina": "[NOME_DISCIPLINA]",
  "dificuldade": "medio" ou "dificil",
  "explicacao": "Baseado nos apontamentos do professor: [explicação detalhada]",
  "referencia": "Apontamentos Prof. - [Tópico]",
  "fonte_material": "professor",
  "legenda": "📚 Material extraído de aula presencial",
  "prioridade_selecao": 0.7
}
```

## 🤖 Scripts para IA - Copie e Cole estes Prompts

**📋 INSTRUÇÃO DE USO:**

Os scripts abaixo são para serem copiados e usados com IAs (Claude, ChatGPT, etc.) para gerar perguntas seguindo o padrão do sistema. Escolha o script apropriado conforme o tipo de material.

**🎯 QUANDO USAR CADA SCRIPT:**

| Tipo de Material | Script a Usar | Identificação |
|-------------------|----------------|---------------|
| 📚 **PDF da Universidade** | Script 1 (Material Oficial) | Unidades, Módulos, Bibliografia |
| 📖 **Apostila do Curso** | Script 1 (Material Oficial) | Material estruturado/oficial |
| 📝 **Livro Didático** | Script 1 (Material Oficial) | Capítulos, seções numeradas |
| 👨‍🏫 **Apontamentos de Aula** | Script 2 (Material Professor) | Slides, explicações exclusivas |
| 🎓 **Notas Pessoais** | Script 2 (Material Professor) | Comentários, observações extras |

### 📚 Script 1: Perguntas de Material Didático Oficial

**🎯 USE ESTE SCRIPT PARA:**
- Material fornecido pela universidade (PDFs, livros didáticos)
- Apostilas oficiais do curso
- Conteúdo de módulos/unidades estruturadas
- Material bibliográfico recomendado

---
**🤖 PROMPT PARA INTELIGÊNCIA ARTIFICIAL (Claude, ChatGPT, etc.):**

```
Atue como um especialista em elaboração de questões para ensino superior baseadas em material didático oficial.

REGRAS OBRIGATÓRIAS:
1. NUNCA crie perguntas de nível fácil - apenas MÉDIO e DIFÍCIL
2. SEMPRE base as perguntas no material didático fornecido (PDF, apostila, livro)
3. SEMPRE inclua todos os campos obrigatórios no JSON
4. SEMPRE crie explicações detalhadas começando com "Conforme descrito no material:"
5. SEMPRE referencie a fonte específica (ex: "Unidade 1 - Tema 2")

ESTRUTURA DA PERGUNTA:
- Enunciado: Deve referenciar conceitos do material didático
- 4 alternativas: 1 correta detalhada + 3 distratores plausíveis
- Explicação: Mínimo 2-3 linhas com fundamentação teórica
- Categoria: Formato "Unidade X - Tema Y" ou similar da fonte

FOCOS POR NÍVEL:
MÉDIO:
- Conceitos fundamentais e suas aplicações
- Relação entre diferentes tópicos
- Interpretação de definições e processos
- Classificações e características principais

DIFÍCIL:
- Análise crítica de conceitos complexos
- Integração entre múltiplos tópicos
- Aplicações práticas avançadas
- Resolução de problemas elaborados

PARÂMETROS TÉCNICOS (INFORMAR SEMPRE):
- Disciplina: [NOME COMPLETO DA DISCIPLINA]
- Período: [1, 2, 3, 4, etc. conforme o curso]
- Quantidade: [NÚMERO DE PERGUNTAS DESEJADAS]
- Material fonte: [TÍTULO/CAPÍTULO DO MATERIAL]

TEMPLATE JSON OBRIGATÓRIO:
{
  "pergunta": "Conforme apresentado no material sobre [TÓPICO], [SITUAÇÃO/PERGUNTA]?",
  "opcoes": [
    "[RESPOSTA CORRETA COM DETALHES]",
    "[DISTRATOR PLAUSÍVEL 1]",
    "[DISTRATOR PLAUSÍVEL 2]",
    "[DISTRATOR PLAUSÍVEL 3]"
  ],
  "resposta_correta": "[REPETIR RESPOSTA CORRETA EXATA]",
  "categoria": "Unidade X - Tema Y",
  "periodo": [NÚMERO DO PERÍODO],
  "disciplina": "[NOME COMPLETO DA DISCIPLINA]",
  "dificuldade": "medio" ou "dificil",
  "explicacao": "Conforme descrito no material: [EXPLICAÇÃO DETALHADA]",
  "referencia": "[FONTE ESPECÍFICA - ex: Unidade 1 Tema 2 DISCIPLINA.pdf]",
  "fonte_material": "oficial",
  "legenda": "📖 Material didático oficial",
  "prioridade_selecao": 0.3
}

APÓS ESTE PROMPT, FORNEÇA:
1. Material didático (PDF, texto, imagens)
2. Nome completo da disciplina
3. Período/semestre do curso
4. Tópicos específicos a serem abordados
5. Número de perguntas desejadas

EXEMPLOS DE USO PARA DIFERENTES DISCIPLINAS:

ENFERMAGEM:
"Baseado no PDF da Unidade 2 sobre Anatomia Cardiovascular, crie 8 perguntas para MORFOFISIOLOGIA II, período 2, cobrindo: estrutura cardíaca, circulação, sistema de condução."

DIREITO:
"Baseado na apostila do Módulo 3 sobre Processo Civil, crie 6 perguntas para DIREITO PROCESSUAL CIVIL, período 4, cobrindo: petição inicial, citação, contestação."

MEDICINA:
"Baseado no livro-texto Capítulo 15 sobre Farmacologia, crie 10 perguntas para FARMACOLOGIA BÁSICA, período 3, cobrindo: farmacocinética, farmacodinâmica, interações."

ADMINISTRAÇÃO:
"Baseado na Unidade 4 sobre Gestão Financeira, crie 12 perguntas para ADMINISTRAÇÃO FINANCEIRA, período 6, cobrindo: fluxo de caixa, análise de investimentos, custo de capital."
```

---

### 👨‍🏫 Script 2: Perguntas de Material do Professor

**🎯 USE ESTE SCRIPT PARA:**
- Apontamentos de aulas presenciais
- Slides específicos do professor
- Explicações complementares em sala
- Material exclusivo não oficial

---
**🤖 PROMPT PARA INTELIGÊNCIA ARTIFICIAL (Claude, ChatGPT, etc.):**

```
Atue como um especialista em elaboração de questões para ensino superior. 

REGRAS OBRIGATÓRIAS:
1. NUNCA crie perguntas de nível fácil - apenas MÉDIO e DIFÍCIL
2. SEMPRE use o formato: 👨‍🏫 **[PROFESSOR]** no início da pergunta
3. SEMPRE base as perguntas em "apontamentos do professor" ou "explicado em aula"
4. SEMPRE inclua todos os campos obrigatórios no JSON
5. SEMPRE crie explicações detalhadas começando com "Baseado nos apontamentos do professor:"

ESTRUTURA DA PERGUNTA:
- Enunciado: Deve referenciar explicitamente material de aula presencial
- 4 alternativas: 1 correta detalhada + 3 distratores plausíveis  
- Explicação: Mínimo 2-3 linhas com fundamentação científica/teórica
- Categoria: Formato adaptável à disciplina (ex: "Tópico - Subtópico")

FOCOS POR NÍVEL:
MÉDIO:
- Aplicação de conceitos em situações práticas
- Correlação entre teoria e prática
- Comparação entre diferentes abordagens/sistemas
- Análise de mecanismos/processos específicos

DIFÍCIL:
- Integração de múltiplos conceitos
- Análise de casos complexos/patológicos
- Correlações interdisciplinares
- Aplicações em diagnóstico/resolução de problemas

PARÂMETROS TÉCNICOS (INFORMAR SEMPRE):
- Disciplina: [NOME COMPLETO DA DISCIPLINA]
- Período: [1, 2, 3, 4, etc. conforme o curso]
- Quantidade: [NÚMERO DE PERGUNTAS DESEJADAS]
- Tópicos: [LISTAR TÓPICOS ESPECÍFICOS DO MATERIAL]

TEMPLATE JSON OBRIGATÓRIO:
{
  "pergunta": "👨‍🏫 **[PROFESSOR]** Segundo explicado em aula sobre [TÓPICO], [SITUAÇÃO/PERGUNTA]?",
  "opcoes": [
    "[RESPOSTA CORRETA COM DETALHES]",
    "[DISTRATOR PLAUSÍVEL 1]",
    "[DISTRATOR PLAUSÍVEL 2]", 
    "[DISTRATOR PLAUSÍVEL 3]"
  ],
  "resposta_correta": "[REPETIR RESPOSTA CORRETA EXATA]",
  "categoria": "[TÓPICO PRINCIPAL] - [SUBTÓPICO]",
  "periodo": [NÚMERO DO PERÍODO],
  "disciplina": "[NOME COMPLETO DA DISCIPLINA]",
  "dificuldade": "medio" ou "dificil",
  "explicacao": "Baseado nos apontamentos do professor: [EXPLICAÇÃO DETALHADA]",
  "referencia": "Apontamentos Prof. - [TÓPICO]",
  "fonte_material": "professor",
  "legenda": "📚 Material extraído de aula presencial",
  "prioridade_selecao": 0.7
}

APÓS ESTE PROMPT, FORNEÇA:
1. Material/imagens dos apontamentos do professor
2. Nome completo da disciplina
3. Período/semestre do curso
4. Tópicos específicos a serem abordados
5. Número de perguntas desejadas

EXEMPLOS DE USO PARA DIFERENTES DISCIPLINAS:

ENFERMAGEM:
"Baseado nas imagens sobre Sistema Endócrino, crie 10 perguntas para MORFOFISIOLOGIA II, período 2, cobrindo: sinalização celular, hormônios, feedback negativo."

DIREITO:
"Baseado nos apontamentos sobre Direitos Fundamentais, crie 8 perguntas para DIREITO CONSTITUCIONAL, período 3, cobrindo: princípios, garantias, limitações."

MEDICINA:
"Baseado no material sobre Patologia Cardiovascular, crie 12 perguntas para PATOLOGIA GERAL, período 4, cobrindo: aterosclerose, infarto, insuficiência cardíaca."

ADMINISTRAÇÃO:
"Baseado nas aulas sobre Gestão de Pessoas, crie 6 perguntas para RECURSOS HUMANOS, período 5, cobrindo: liderança, motivação, conflitos."
```

##### **Como Sincronizar Perguntas do Professor:**

1. **Adicione as perguntas** no `perguntas_test.json` usando o formato acima
2. **Extraia perguntas do professor** (se necessário):
   ```bash
   python extrair_professor.py  # Cria perguntas_professor_apenas.json
   ```
3. **Sincronize** com o banco principal:
   ```bash
   python sincronizar_perguntas.py --staging perguntas_professor_apenas.json
   ```

##### **Distribuição Automática 70/30:**
- Em disciplinas com perguntas do professor, o sistema automaticamente seleciona:
  - **70% perguntas** marcadas como `fonte_material: "professor"`
  - **30% perguntas** do material oficial da universidade
- Interface mostra **badge verde** com ícone de professor para perguntas de aula presencial

##### **Exemplo de Uso Completo:**

**Para MORFOFISIOLOGIA II - Sistema Endócrino:**
```json
{
  "pergunta": "👨‍🏫 **[PROFESSOR]** Segundo explicado em aula sobre tipos de sinalização celular, qual a principal característica que diferencia a sinalização parácrina da endócrina?",
  "opcoes": [
    "Sinalização parácrina atua localmente entre células vizinhas, enquanto endócrina atua sistemicamente",
    "Sinalização parácrina utiliza apenas neurotransmissores, endócrina apenas hormônios proteicos",
    "Sinalização parácrina é mais lenta que endócrina devido à distância percorrida",
    "Sinalização parácrina requer receptores intracelulares, endócrina apenas de membrana"
  ],
  "resposta_correta": "Sinalização parácrina atua localmente entre células vizinhas, enquanto endócrina atua sistemicamente",
  "categoria": "Sistema Endócrino - Tipos de Sinalização",
  "periodo": 2,
  "disciplina": "MORFOFISIOLOGIA II",
  "dificuldade": "medio",
  "explicacao": "Baseado nos apontamentos do professor: A sinalização parácrina caracteriza-se pela ação local sobre células vizinhas, sem necessidade de transporte sistêmico, enquanto a sinalização endócrina envolve hormônios que percorrem a corrente sanguínea para atingir células-alvo distantes.",
  "referencia": "Apontamentos Prof. - Sistema Endócrino",
  "fonte_material": "professor",
  "legenda": "📚 Material extraído de aula presencial",
  "prioridade_selecao": 0.7
}
```

### 2. **Restaurar Backup**
- O backup das perguntas de recuperação está em `data/perguntas_recuperacao_backup.json`.
- Para restaurar, use o botão "Redefinir Banco de Perguntas" no painel admin ou copie manualmente o arquivo de backup sobre o arquivo principal.

### 3. **Alterar Admin**
- Altere o email ou senha do admin pelo painel admin em "Configurações do Sistema".
- O arquivo de configuração do admin é `admin_user.json`.

### 4. **Exportar Banco de Perguntas**
- Use o botão "Exportar Banco de Perguntas" no painel admin para baixar o arquivo JSON atual.

### 5. **Atualizar Dependências**
- As dependências estão em `requirements.txt`.
- Para atualizar:
  ```bash
  pip install -r requirements.txt
  ```

### 6. **Rodar Scripts de Análise**
- O script `analise_respostas.py` gera um relatório de perguntas com respostas desbalanceadas.
- Execute com:
  ```bash
  python analise_respostas.py
  ```
- O relatório será salvo como `relatorio_comprimento_respostas.txt`.

---
### **Passo a Passo para Deploy**
> **⚠️ IMPORTANTE: Esta seção foi testada e está funcionando. NÃO ALTERE estes comandos!**

#### 1. **Copie os arquivos para a pasta deploy**
No PowerShell, execute:
```powershell
cd "G:\Meu Drive\quiz\quiz_1"
copy app.py deploy\
copy requirements.txt deploy\
copy admin_user.json deploy\
copy Dockerfile deploy\
robocopy data deploy\data /E
robocopy static deploy\static /E
robocopy templates deploy\templates /E
```
> **Obs:** Sempre copie os arquivos do projeto para a pasta `deploy` antes de cada build/deploy!

#### 2. **Acesse a pasta deploy**
```powershell
cd "G:\Meu Drive\quiz\quiz_1\deploy"
```

#### 3. **Build e deploy no Google Cloud Run**
```powershell
gcloud builds submit --tag gcr.io/quizenfermagem/quiz_cloud
gcloud run deploy quiz-cloud --image gcr.io/quizenfermagem/quiz_cloud --platform managed --region us-central1 --allow-unauthenticated
```

#### 4. **Acesse o sistema**
- O terminal mostrará a URL pública do seu app (ex: `https://quiz-cloud-xxxxxx.a.run.app`)
- Acesse no navegador para testar.

#### 5. **Ver logs do Cloud Run**
```powershell
gcloud run services logs read quiz-cloud --project=quizenfermagem --region=us-central1 --limit=50
```

---

## 📁 Estrutura Recomendada

```
quiz_cloud/
├── app.py
├── requirements.txt
├── app.yaml
├── data/
├── static/
├── templates/
├── admin_user.json
├── README.md
└── ...
```

---

## 💡 Dicas de Manutenção
- Sempre faça backup dos arquivos `data/` e `admin_user.json` antes de atualizar.
- Use o painel admin para tarefas comuns de manutenção.
- Para debug, use logs do Flask ou do Google Cloud.
- Para restaurar o sistema, basta copiar os arquivos de backup sobre os arquivos principais.

---

## 📞 Suporte
Se precisar de ajuda para manutenção, atualização ou deploy, consulte este README ou entre em contato com o desenvolvedor responsável.

---

**Projeto: quiz_cloud**

# 🎯 Quiz Interativo - Sistema de Perguntas e Respostas

Um sistema moderno e interativo de quiz desenvolvido em Flask, com design responsivo e funcionalidades avançadas para estudantes de enfermagem.

## ✨ Características Principais

### 🎨 Design Moderno
- **Interface responsiva** com design glassmorphism
- **Gradientes atrativos** e animações suaves
- **Tipografia moderna** usando Inter Font
- **Ícones FontAwesome** para melhor experiência visual
- **Animações CSS** e efeitos hover
- **Compatibilidade mobile** completa

### 📚 Funcionalidades do Quiz
- **Quiz Normal**: Perguntas por período e disciplina
- **Quiz Recuperação**: Foco em tópicos específicos (ESF)
- **Sistema de pontuação** em tempo real
- **Timer configurável** para cada questão
- **Feedback imediato** com explicações
- **Acessibilidade** com leitura de tela (TTS)
- **Progresso visual** com barras animadas

### 🔐 Área Administrativa
- **Login seguro** com Google OAuth
- **Dashboard moderno** com estatísticas
- **Gerenciamento completo** de perguntas
- **Sistema de backup** automático
- **Interface intuitiva** para administradores

## 🚀 Tecnologias Utilizadas

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript
- **Design**: CSS Grid, Flexbox, Glassmorphism
- **Fontes**: Inter (Google Fonts)
- **Ícones**: FontAwesome 6.0
- **Autenticação**: Google OAuth
- **Dados**: JSON (perguntas e configurações)

## 📁 Estrutura do Projeto

```
quiz_1/
├── app.py                          # Aplicação principal Flask
├── data/                           # Dados do quiz
│   ├── perguntas.json             # Perguntas principais
│   └── perguntas_recuperacao.json # Perguntas de recuperação (ESF)
├── static/                         # Arquivos estáticos
│   ├── style.css                  # Estilos globais
│   ├── quiz.js                    # JavaScript do quiz
│   ├── admin.js                   # JavaScript do admin
│   ├── admin-dashboard.css        # Estilos do dashboard admin
│   └── script.js                  # Scripts auxiliares
├── templates/                      # Templates HTML
│   ├── index.html                 # Página inicial
│   ├── quiz.html                  # Interface do quiz
│   ├── resultado.html             # Página de resultados
│   └── admin/                     # Área administrativa
│       ├── login.html             # Login admin
│       ├── dashboard.html         # Dashboard admin moderno
│       └── setup.html             # Configuração inicial
├── deploy/                        # Versão de produção
│   ├── Dockerfile                 # Configuração Docker
│   ├── app.py                     # App otimizado para produção
│   └── requirements.txt           # Dependências de produção
├── requirements.txt               # Dependências de desenvolvimento
└── README.md                      # Documentação
```

## 🎯 Páginas Principais

### 1. Página Inicial (`/`)
- **Seleção de quiz** (Normal/Recuperação)
- **Filtros por período** e disciplina
- **Estatísticas** em tempo real
- **Design responsivo** com cards modernos

### 2. Interface do Quiz (`/quiz`)
- **Perguntas dinâmicas** com opções interativas
- **Timer visual** com animações
- **Progresso em tempo real**
- **Feedback imediato** com cores
- **Acessibilidade** com TTS

### 3. Resultados (`/resultado`)
- **Pontuação detalhada** com animações
- **Análise de performance** com emojis
- **Revisão de respostas** com explicações
- **Compartilhamento** de resultados

### 4. Área Administrativa
- **Login seguro** com Google
- **Dashboard moderno** com métricas avançadas
- **CRUD completo** de perguntas
- **Backup automático** dos dados
- **Analytics em tempo real**

## 🎨 Design System

### Cores Principais
- **Primária**: `#667eea` → `#764ba2` (Gradiente)
- **Sucesso**: `#27ae60` → `#2ecc71` (Gradiente)
- **Erro**: `#e74c3c` → `#c0392b` (Gradiente)
- **Aviso**: `#f39c12` → `#f1c40f` (Gradiente)

### Tipografia
- **Família**: Inter (Google Fonts)
- **Pesos**: 300, 400, 500, 600, 700, 800
- **Hierarquia**: Títulos grandes, texto legível

### Componentes
- **Cards**: Glassmorphism com blur
- **Botões**: Gradientes com hover effects
- **Formulários**: Campos modernos com focus states
- **Progresso**: Barras animadas com shimmer

## 🚀 Como Executar

### Pré-requisitos
- Python 3.7+
- pip (gerenciador de pacotes)

### Instalação Local

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd quiz_1
```

2. **Crie um ambiente virtual**
```bash
python -m venv .venv
```

3. **Ative o ambiente virtual**
```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

4. **Instale as dependências**
```bash
pip install -r requirements.txt
```

5. **Execute a aplicação**
```bash
python app.py
```

6. **Acesse no navegador**
```
http://localhost:8080
```

## ☁️ Deploy em Produção

### 🐳 Deploy com Docker

#### 1. **Usando a pasta deploy (Recomendado)**
```bash
cd deploy
docker build -t quiz-enfermagem .
docker run -p 8080:8080 -e PERGUNTAS_JSON_PATH=data/perguntas.json quiz-enfermagem
```

#### 2. **Deploy direto**
```bash
docker build -t quiz-enfermagem .
docker run -p 8080:8080 -e PERGUNTAS_JSON_PATH=data/perguntas.json quiz-enfermagem
```

### 🌐 Deploy no Google Cloud Run

#### 1. **Configuração inicial**
```bash
# Instale o Google Cloud CLI
# Configure o projeto
gcloud config set project SEU_PROJECT_ID
```

#### 2. **Build e deploy**
```bash
cd deploy
gcloud builds submit --tag gcr.io/SEU_PROJECT_ID/quiz-enfermagem
gcloud run deploy quiz-enfermagem \
  --image gcr.io/SEU_PROJECT_ID/quiz-enfermagem \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars PERGUNTAS_JSON_PATH=data/perguntas.json
```

#### 3. **Acesse a aplicação**
- A URL será exibida no terminal após o deploy
- Exemplo: `https://quiz-enfermagem-xxxxx.a.run.app`

### 🐳 Deploy no Docker Hub

#### 1. **Build da imagem**
```bash
docker build -t seu-usuario/quiz-enfermagem:latest .
```

#### 2. **Push para Docker Hub**
```bash
docker push seu-usuario/quiz-enfermagem:latest
```

#### 3. **Deploy em qualquer servidor**
```bash
docker pull seu-usuario/quiz-enfermagem:latest
docker run -p 8080:8080 seu-usuario/quiz-enfermagem:latest
```

### 🚀 Deploy no Heroku

#### 1. **Instale o Heroku CLI**
```bash
# Windows
# Baixe e instale do site oficial

# macOS
brew install heroku/brew/heroku
```

#### 2. **Configure o projeto**
```bash
heroku login
heroku create quiz-enfermagem-app
```

#### 3. **Deploy**
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

#### 4. **Abra a aplicação**
```bash
heroku open
```

### 🔧 Deploy Manual em VPS

#### 1. **Prepare o servidor**
```bash
# Instale Python, pip e nginx
sudo apt update
sudo apt install python3 python3-pip nginx
```

#### 2. **Configure o projeto**
```bash
# Clone o repositório
git clone <url-do-repositorio>
cd quiz_1

# Instale dependências
pip3 install -r requirements.txt
```

#### 3. **Configure o Gunicorn**
```bash
# Instale gunicorn
pip3 install gunicorn

# Crie um serviço systemd
sudo nano /etc/systemd/system/quiz-enfermagem.service
```

Conteúdo do arquivo de serviço:
```ini
[Unit]
Description=Quiz Enfermagem
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/quiz_1
Environment="PATH=/path/to/quiz_1/.venv/bin"
ExecStart=/path/to/quiz_1/.venv/bin/gunicorn --workers 3 --bind unix:quiz-enfermagem.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

#### 4. **Configure o Nginx**
```bash
sudo nano /etc/nginx/sites-available/quiz-enfermagem
```

Conteúdo da configuração:
```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/quiz_1/quiz-enfermagem.sock;
    }
}
```

#### 5. **Ative o serviço**
```bash
sudo ln -s /etc/nginx/sites-available/quiz-enfermagem /etc/nginx/sites-enabled
sudo systemctl start quiz-enfermagem
sudo systemctl enable quiz-enfermagem
sudo systemctl restart nginx
```

## 🔧 Configurações de Produção

### Variáveis de Ambiente
```bash
# Configurações do Flask
export FLASK_ENV=production
export FLASK_DEBUG=0

# Configurações do servidor
export PORT=8080
export HOST=0.0.0.0
```

### Configurações de Segurança
- ✅ **HTTPS habilitado** em produção
- ✅ **Headers de segurança** configurados
- ✅ **CORS configurado** adequadamente
- ✅ **Rate limiting** implementado
- ✅ **Validação de entrada** robusta

### Monitoramento
- 📊 **Logs estruturados** para análise
- 🔍 **Métricas de performance** em tempo real
- ⚠️ **Alertas automáticos** para erros
- 📈 **Dashboard de analytics** integrado

## 🆕 Atualizações Implementadas

### Sistema de Perguntas do Professor (v1.2)

#### **Funcionalidades Implementadas:**

##### 1. **Destaque Visual das Perguntas do Professor**
- ✅ **Badge verde** na interface do quiz com ícone `fas fa-chalkboard-teacher`
- ✅ **Legenda explicativa**: "📚 Material extraído de aula presencial"
- ✅ **Prefixo visual** no enunciado: `👨‍🏫 **[PROFESSOR]**`

##### 2. **Distribuição Inteligente 70/30**
- ✅ **Lógica automática** no `app.py` (linhas 511-545)
- ✅ **70% perguntas do professor** quando disponíveis
- ✅ **30% material oficial** da universidade
- ✅ **Fallback inteligente** quando não há perguntas suficientes

##### 3. **Novos Campos no Banco de Dados**
- ✅ `fonte_material`: "professor" | "oficial"
- ✅ `legenda`: "📚 Material extraído de aula presencial"
- ✅ `prioridade_selecao`: 0.7 (para cálculos de distribuição)

##### 4. **Scripts de Sincronização**
- ✅ **sincronizar_perguntas.py**: Integração com novos campos
- ✅ **extrair_professor.py**: Extração específica de perguntas do professor
- ✅ **Deduplicação inteligente**: Evita perguntas repetidas

##### 5. **Interface Aprimorada**
- ✅ **CSS customizado** para badge do professor
- ✅ **Template atualizado** (`templates/quiz.html`)
- ✅ **Detecção automática** do tipo de pergunta

#### **Arquivos Modificados:**

1. **app.py** (linhas 506-545): Lógica de distribuição 70/30
2. **templates/quiz.html** (linhas 410-415, 109-126): Interface e CSS
3. **perguntas_test.json**: Formato atualizado com novos campos
4. **sincronizar_perguntas.py**: Suporte aos novos campos
5. **extrair_professor.py**: Script de extração específica

#### **Estatísticas Atuais:**
- 📊 **42 perguntas do professor** criadas para MORFOFISIOLOGIA II
  - 12 sobre Sistema Endócrino (Sinalização)
  - 10 sobre Eixo Hipotálamo-Hipófise
  - 20 sobre Sistema Reprodutor
- 📚 **Sistema completo** para material oficial e do professor
- 🎯 **100% das perguntas** em níveis médio/difícil
- ✅ **Distribuição automática 70/30** funcionando
- 🤖 **2 Scripts de IA** disponíveis (oficial + professor)

#### **Como Verificar se Está Funcionando:**

1. **Inicie um quiz** de MORFOFISIOLOGIA II, período 2
2. **Observe o badge verde** nas perguntas do professor
3. **Verifique a distribuição**: ~70% com badge, ~30% sem badge
4. **Confira o log** do app para ver a seleção de perguntas

#### **Comandos de Teste:**
```bash
# Verificar perguntas do professor no banco
python -c "import json; data=json.load(open('data/perguntas.json', 'r', encoding='utf-8')); prof=[q for q in data if q.get('fonte_material')=='professor']; print(f'Perguntas do professor: {len(prof)}')"

# Testar sincronização
python extrair_professor.py  # Extrai perguntas do professor
python sincronizar_perguntas.py --staging perguntas_professor_apenas.json --dry-run

# Executar aplicação
python app.py
```

## 🛠️ Manutenção

### Backup Automático
- **Dados**: Backup automático das perguntas
- **Configurações**: Backup das configurações do admin
- **Sessões**: Limpeza automática de sessões antigas

### Atualizações
```bash
# Atualizar dependências
pip install -r requirements.txt --upgrade

# Reiniciar aplicação
sudo systemctl restart quiz-enfermagem
```

### Logs
```bash
# Ver logs da aplicação
sudo journalctl -u quiz-enfermagem -f

# Ver logs do nginx
sudo tail -f /var/log/nginx/access.log
```

## 📞 Suporte

Para suporte técnico ou dúvidas sobre deploy:
- 📧 **Email**: [seu-email@exemplo.com]
- 📱 **Telegram**: [@seu-usuario]
- 🌐 **Documentação**: [link-para-docs]

---

**Versão**: 2.1.0 - Sistema de Perguntas do Professor  
**Última atualização**: Janeiro 2025  
**Status**: ✅ Pronto para produção