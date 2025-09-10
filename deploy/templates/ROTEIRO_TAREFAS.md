# 🗺️ Roteiro de Tarefas - Novo Projeto Quiz

Este documento lista as tarefas planejadas para o desenvolvimento do Novo Projeto Quiz e seu status.

## ✅ Estrutura Base e Configuração Inicial (Concluído)

- [x] Criação da estrutura de pastas (`data`, `templates`, `static`)
- [x] Criação do arquivo `app.py` inicial com Flask e rotas básicas
- [x] Criação dos arquivos JSON de exemplo (`perguntas.json`, `perguntas_recuperacao.json`)
- [x] Criação dos templates HTML básicos (`index.html`, `quiz.html`, `resultado.html`)
- [x] Configuração do logging básico no `app.py`
- [x] Criação do arquivo `LEIAME.md`
- [x] Criação deste arquivo `ROTEIRO_TAREFAS.md` e atualização inicial

## 🧠 Funcionalidades do Quiz Principal

- [ ] Implementar lógica de verificação de resposta e pontuação na rota `/responder`
- [ ] Melhorar a exibição das perguntas e opções no `quiz.html` (ex: letras A, B, C, D)
- [ ] Melhorar a exibição dos resultados no `resultado.html` (ex: mostrar respostas dadas, corretas, explicações)
- [ ] Adicionar filtros na `index.html` para iniciar quiz por período e/ou disciplina
- [ ] Implementar a lógica de filtragem de perguntas no `app.py` para o Quiz Principal (por período e/ou disciplina)
- [ ] Adicionar feedback visual imediato para respostas corretas/incorretas (opcional, via JS)
- [ ] Mostrar explicações das respostas no final do quiz ou após cada pergunta (Quiz Principal)

## 🔄 Funcionalidades do Quiz de Recuperação

- [ ] Criar rota e template para listar disciplinas de recuperação disponíveis
- [ ] Criar rota e template para listar tópicos de uma disciplina de recuperação selecionada
- [ ] Criar rota para iniciar o quiz de recuperação com base na disciplina e tópico escolhidos
- [ ] Adaptar a lógica de exibição de perguntas, respostas e resultados para o quiz de recuperação

## 🛠️ Área Administrativa (Gerenciamento de Perguntas)

- [ ] Criar interface (template `admin.html`) para adicionar novas perguntas de recuperação
- [ ] Implementar funcionalidade de editar perguntas de recuperação existentes
- [ ] Implementar funcionalidade de excluir perguntas de recuperação (já iniciada no `app.py`)
- [ ] Criar interface para adicionar, editar e excluir perguntas do quiz principal (`perguntas.json`)
- [ ] Adicionar validação robusta para os dados das perguntas (campos obrigatórios, formato das opções, etc.)
- [ ] Implementar funcionalidade de upload de arquivos JSON de perguntas (recuperação)

## ✨ Melhorias Gerais e Interface

- [ ] Criar um arquivo `static/style.css` básico e linkar nos templates para melhorar a aparência
- [ ] Melhorar o design geral e a usabilidade das páginas
- [ ] Adicionar navegação clara entre as diferentes seções do quiz (principal, recuperação, admin)
- [ ] Implementar persistência de dados de forma mais robusta (além de JSON, se necessário no futuro, ex: SQLite)

## 🚀 Funcionalidades Adicionais (Futuras - Pós-MVP)

- [ ] Sistema de login/usuários (para salvar progresso, estatísticas individuais)
- [ ] Banco de dados mais robusto (ex: SQLite integrado, PostgreSQL) para gerenciamento de usuários e perguntas
- [ ] Geração de estatísticas de desempenho por usuário, disciplina, período
- [ ] Modo de estudo com revisão de perguntas erradas
- [ ] Ranking de usuários (opcional)