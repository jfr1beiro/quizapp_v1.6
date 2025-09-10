# Novo Projeto Quiz Interativo

Bem-vindo ao Novo Projeto Quiz Interativo! Este sistema foi desenvolvido para criar e gerenciar quizzes de forma flexível, com suporte para um quiz principal e um modo de recuperação por disciplina e tópico.

## 🚀 Tecnologias Utilizadas

*   **Python 3**: Linguagem de programação principal.
*   **Flask**: Microframework web para desenvolvimento da aplicação.
*   **JSON**: Formato para armazenamento dos dados das perguntas.
*   **HTML/CSS/JavaScript**: Para a interface do usuário no navegador.

## 📂 Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
G:\Meu Drive\quiz\quiz_1\
├── app.py                     # Arquivo principal da aplicação Flask
├── data/
│   ├── perguntas.json           # Perguntas do quiz principal
│   └── perguntas_recuperacao.json # Perguntas do quiz de recuperação
├── templates/
│   ├── index.html             # Página inicial
│   ├── quiz.html              # Página de exibição das perguntas do quiz
│   ├── resultado.html         # Página de resultados do quiz
│   └── admin.html             # Página de administração (a ser desenvolvida)
├── static/
│   └── style.css              # Arquivo de estilos (exemplo)
├── LEIAME.md                  # Este arquivo
└── ROTEIRO_TAREFAS.md         # Roteiro com o planejamento e progresso do projeto
```

## ⚙️ Como Configurar e Executar

### Pré-requisitos

*   Python 3.x instalado.
*   Flask instalado. Se não tiver, instale com:
    ```bash
    pip install Flask
    ```

### Passos para Executar

1.  **Navegue até a pasta do projeto** no seu terminal:
    ```bash
    cd "G:\Meu Drive\quiz\quiz_1"
    ```
2.  **Execute o arquivo `app.py`**:
    ```bash
    python app.py
    ```
    Ou, se preferir usar o Flask CLI (após configurar `FLASK_APP=app.py`):
    ```bash
    flask run
    ```
3.  **Acesse no navegador**:
    Abra seu navegador e acesse o endereço fornecido no terminal (geralmente `http://127.0.0.1:8080/` ou `http://localhost:8080/`).

## 📝 Como Alimentar o Sistema com Perguntas

### Quiz Principal (`data/perguntas.json`)

Este arquivo deve ser uma lista de objetos JSON, onde cada objeto representa uma pergunta.

**Formato da Pergunta:**
```json
[
  {
    "pergunta": "Qual é a capital da França?",
    "opcoes": ["Berlim", "Madri", "Paris", "Lisboa"],
    "resposta_correta": "Paris",
    "categoria": "Geografia",
    "periodo": 1,
    "disciplina": "Conhecimentos Gerais",
    "dificuldade": "facil",
    "explicacao": "Paris é a capital e a maior cidade da França."
  }
]
```

### Quiz de Recuperação (`data/perguntas_recuperacao.json`)

Este arquivo é um objeto JSON onde as chaves são os nomes das disciplinas. Cada disciplina contém um objeto de tópicos, e cada tópico contém uma lista de perguntas no mesmo formato do quiz principal, mas com os campos adicionais `disciplina` e `topico` preenchidos.

**Formato:**
```json
{
  "NomeDaDisciplina": {
    "NomeDoTopico 1": [
      {
        "pergunta": "Pergunta de recuperação sobre o tópico 1?",
        "opcoes": ["A", "B", "C", "D"],
        "resposta_correta": "A",
        "categoria": "Categoria Exemplo",
        "disciplina": "NomeDaDisciplina",
        "topico": "NomeDoTopico 1",
        "dificuldade": "medio",
        "explicacao": "Explicação da resposta."
      }
    ]
  }
}
```

## 🗺️ Funcionalidades Planejadas

Consulte o arquivo ROTEIRO_TAREFAS.md para ver o planejamento completo e o progresso das funcionalidades.

---
*Última atualização: {DATA_ATUAL}*