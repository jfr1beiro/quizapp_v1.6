# 🚀 Quiz Cloud - Sistema de Quiz para Enfermagem

Este projeto é uma evolução do sistema original "Quiz Interativo". Ele foi preparado para manutenção, atualização e deploy em nuvem (Google Cloud), sem afetar o projeto anterior.

---

## 🛠️ Manutenção e Atualização

### 1. **Editar Perguntas**
- Os arquivos de perguntas ficam em `data/perguntas.json` (quiz comum) e `data/perguntas_recuperacao_organizado.json` (recuperação ESF).
- Para editar, use um editor de texto ou a interface admin (`/admin`).
- Sempre faça backup antes de grandes alterações.

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

## ☁️ Deploy/Debug no Google Cloud (novo projeto: quiz_cloud)

### 1. **Clone o projeto para uma nova pasta**
```bash
cp -r quiz_1 quiz_cloud
cd quiz_cloud
```

### 2. **Renomeie o projeto no README e arquivos de configuração**
- Altere o nome do projeto para `quiz_cloud` onde desejar.

### 3. **Prepare o ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows
pip install -r requirements.txt
```

### 4. **Adicione arquivos de deploy do Google Cloud**
- Crie um arquivo `app.yaml` na raiz:
  ```yaml
  runtime: python39
  entrypoint: gunicorn -b :$PORT app:app
  ```
- (Opcional) Adicione um `Dockerfile` se quiser usar Docker.

### 5. **Debug localmente**
```bash
# Windows PowerShell
$Env:PERGUNTAS_JSON_PATH = "data/perguntas.json"
python app.py
# ou
gunicorn -b 0.0.0.0:8080 app:app
```
Acesse em `http://localhost:8080`.

### 6. **Deploy para Google Cloud App Engine**
- Instale o SDK do Google Cloud e autentique:
  ```bash
  gcloud init
  gcloud auth application-default login
  ```
- Faça deploy:
  ```bash
  gcloud app deploy app.yaml
  ```
- Acesse a URL fornecida pelo Google Cloud.

### 7. **Checklist de Deploy Seguro**
- [ ] Teste localmente antes de subir.
- [ ] Não suba arquivos de backup ou dados sensíveis.
- [ ] Altere as credenciais do admin após o deploy.
- [ ] Use HTTPS em produção.
- [ ] Monitore os logs pelo Google Cloud Console.

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
│   └── script.js                  # Scripts auxiliares
├── templates/                      # Templates HTML
│   ├── index.html                 # Página inicial
│   ├── quiz.html                  # Interface do quiz
│   ├── resultado.html             # Página de resultados
│   └── admin/                     # Área administrativa
│       ├── login.html             # Login admin
│       ├── dashboard.html         # Dashboard admin
│       └── perguntas.html         # Gerenciamento de perguntas
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
- **Dashboard** com métricas
- **CRUD completo** de perguntas
- **Backup automático** dos dados

## 🎨 Design System

### Cores Principais
- **Primária**: `#667eea` → `#764ba2` (Gradiente)
- **Sucesso**: `#27ae60` → `#2ecc71` (Gradiente)
- **Erro**: `#e74c3c` → `#c0392b` (Gradiente)
- **Aviso**: `#f39c12` → `#f1c40f` (Gradiente)

### Tipografia
- **Família**: Inter (Google Fonts)
- **Pesos**: 300, 400, 500, 600, 700
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

### Instalação

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd quiz_1
```

2. **Crie um ambiente virtual**
```bash
python -m venv venv
```

3. **Ative o ambiente virtual**
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

4. **Instale as dependências**
```bash
pip install flask
```

5. **Execute a aplicação**
```bash
python app.py
```

6. **Acesse no navegador**
```
http://localhost:5000
```

## 📊 Funcionalidades Avançadas

### Sistema de Quiz
- **Modo Normal**: Perguntas por período/disciplina
- **Modo Recuperação**: Foco em ESF com tópicos
- **Timer configurável** por questão
- **Pontuação dinâmica** baseada em tempo
- **Feedback visual** imediato

### Acessibilidade
- **Leitura de tela** (TTS) para perguntas
- **Navegação por teclado** completa
- **Contraste adequado** para leitura
- **Textos alternativos** para imagens

### Administração
- **Autenticação Google** segura
- **Dashboard** com métricas em tempo real
- **Gerenciamento CRUD** de perguntas
- **Sistema de backup** automático
- **Interface responsiva** para mobile

## 🎯 Melhorias Implementadas

### Design
- ✅ **Interface moderna** com glassmorphism
- ✅ **Gradientes atrativos** e animações
- ✅ **Responsividade** completa
- ✅ **Tipografia moderna** (Inter)
- ✅ **Ícones FontAwesome** integrados

### Funcionalidades
- ✅ **Sistema de quiz** completo
- ✅ **Timer visual** com animações
- ✅ **Feedback imediato** com cores
- ✅ **Progresso em tempo real**
- ✅ **Acessibilidade** com TTS

### Administração
- ✅ **Login seguro** com Google
- ✅ **Dashboard moderno**
- ✅ **CRUD de perguntas**
- ✅ **Backup automático**
- ✅ **Interface intuitiva**

## 🔧 Configuração

### Variáveis de Ambiente
```bash
# Configurações do Google OAuth (para admin)
GOOGLE_CLIENT_ID=seu_client_id
GOOGLE_CLIENT_SECRET=seu_client_secret

# Configurações do Flask
FLASK_SECRET_KEY=sua_chave_secreta
FLASK_ENV=development
```

### Estrutura de Dados
- **perguntas.json**: Perguntas principais organizadas por período/disciplina
- **perguntas_recuperacao.json**: Perguntas de recuperação (ESF) por tópico

## 📱 Compatibilidade

- ✅ **Desktop**: Chrome, Firefox, Safari, Edge
- ✅ **Mobile**: iOS Safari, Chrome Mobile
- ✅ **Tablet**: iPad, Android tablets
- ✅ **Acessibilidade**: Screen readers, navegação por teclado

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 👥 Autores

- **Desenvolvedor**: [Seu Nome]
- **Design**: Modern UI/UX com glassmorphism
- **Funcionalidades**: Sistema completo de quiz interativo

## 🙏 Agradecimentos

- **Google Fonts** pela tipografia Inter
- **FontAwesome** pelos ícones
- **Flask** pelo framework web
- **Comunidade** pelo feedback e sugestões

---

**🎯 Quiz Interativo** - Transformando o aprendizado em uma experiência interativa e moderna! 