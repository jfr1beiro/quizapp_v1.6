// Variáveis globais
let perguntaAtual = 0;
let pontos = 0;
let totalPerguntas = 0;
let perguntaData = null;
let respostaEnviada = false;
let respostaSelecionada = null;

// Função principal para carregar pergunta
function carregarPergunta() {
    console.log('Carregando pergunta...');
    
    // Mostra loading
    const container = document.getElementById('quiz-container');
    container.innerHTML = `
        <div class="loading-container">
            <div class="loading-spinner"></div>
            <p>Carregando pergunta...</p>
        </div>
    `;
    
    fetch('/proxima_pergunta')
        .then(response => {
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Dados recebidos:', data);
            
            if (data.erro) {
                alert('Erro: ' + data.erro);
                return;
            }
            
            if (data.fim) {
                // Pequeno delay antes de ir para resultado
                setTimeout(() => {
                    window.location.href = '/resultado';
                }, 500);
                return;
            }
            
            // Atualiza variáveis
            perguntaData = data.pergunta;
            perguntaAtual = data.numero;
            totalPerguntas = data.total;
            respostaEnviada = false;
            respostaSelecionada = null;
            
            // Exibe a pergunta
            exibirPergunta(data);
        })
        .catch(error => {
            console.error('Erro:', error);
            container.innerHTML = `
                <div class="erro-container">
                    <h2>Erro ao carregar pergunta</h2>
                    <p>${error.message}</p>
                    <button onclick="carregarPergunta()" class="btn-tentar-novamente">Tentar Novamente</button>
                </div>
            `;
        });
}

// Função para exibir pergunta
function exibirPergunta(data) {
    const container = document.getElementById('quiz-container');
    
    const html = `
        <div class="pergunta-header">
            <div class="progresso">
                <div class="progresso-barra">
                    <div class="progresso-preenchido" style="width: ${(perguntaAtual/totalPerguntas)*100}%"></div>
                </div>
                <span class="progresso-texto">Pergunta ${perguntaAtual} de ${totalPerguntas}</span>
            </div>
            <div class="pontuacao">
                <span class="pontos">Pontos: ${pontos}</span>
            </div>
        </div>
        <div class="pergunta-card">
            <div class="categoria-badge">${data.pergunta.categoria}</div>
            <h2 class="pergunta-texto">${data.pergunta.pergunta}</h2>
            <div class="opcoes-container" style="max-height:40vh;overflow-y:auto;margin-bottom:20px;padding-right:8px;">
                ${data.pergunta.opcoes.map((opcao, index) => `
                    <button class="opcao-btn" onclick="selecionarResposta(${index})" id="opcao-${index}" style="width:100%;text-align:left;">
                        <span class="opcao-letra">${String.fromCharCode(65 + index)}</span>
                        <span class="opcao-texto">${opcao}</span>
                    </button>
                `).join('')}
            </div>
            <div class="feedback-container" id="feedback-container" style="display: none;"></div>
            <div class="instrucoes">
                <p>💡 Clique na resposta ou use as teclas A, B, C, D</p>
            </div>
            <div class="controls" style="position:sticky;bottom:0;background:rgba(255,255,255,0.95);padding:15px 0 0 0;z-index:2;display:flex;flex-wrap:wrap;gap:10px;justify-content:center;">
                <button type="button" class="btn secondary" onclick="voltarInicio()">
                    <i class="fas fa-home"></i>
                    Voltar ao Início
                </button>
                <button type="button" class="btn primary" id="btn-responder" disabled>
                    <i class="fas fa-paper-plane"></i>
                    Responder
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// Função para selecionar resposta (AUTOMÁTICA)
function selecionarResposta(index) {
    if (respostaEnviada) return;
    
    console.log('Selecionando e enviando resposta:', index);
    respostaEnviada = true;
    respostaSelecionada = index;
    
    // Marca a seleção visualmente
    document.getElementById(`opcao-${index}`).classList.add('selecionada');
    
    // Desabilita todas as opções imediatamente
    document.querySelectorAll('.opcao-btn').forEach(btn => {
        btn.disabled = true;
    });
    
    // Mostra feedback de "processando"
    mostrarProcessando();
    
    // Envia resposta automaticamente
    fetch('/responder', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            resposta: String.fromCharCode(65 + respostaSelecionada),
            resposta_correta: perguntaData.resposta_correta,
            opcoes: perguntaData.opcoes
        })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Resposta processada:', data);
        pontos = data.pontos;
        
        // Pequeno delay para mostrar o feedback
        setTimeout(() => {
            mostrarFeedback(data);
        }, 300);
    })
    .catch(error => {
        console.error('Erro ao processar resposta:', error);
        alert('Erro ao processar resposta');
        
        // Reabilita em caso de erro
        respostaEnviada = false;
        document.querySelectorAll('.opcao-btn').forEach(btn => {
            btn.disabled = false;
        });
    });
}

// Função para mostrar "processando"
function mostrarProcessando() {
    const feedbackContainer = document.getElementById('feedback-container');
    feedbackContainer.innerHTML = `
        <div class="feedback feedback-processando">
            <div class="feedback-header">
                <span class="feedback-icon">⏳</span>
                <span class="feedback-texto">Processando...</span>
            </div>
        </div>
    `;
    feedbackContainer.style.display = 'block';
}

// Função para mostrar feedback (COM AVANÇO AUTOMÁTICO)
function mostrarFeedback(data) {
    console.log('Mostrando feedback:', data);
    
    // Marca as opções
    document.querySelectorAll('.opcao-btn').forEach((btn, index) => {
        // Remove classe de selecionada
        btn.classList.remove('selecionada');
        
        // Marca a resposta do usuário
        if (index === respostaSelecionada) {
            if (data.acertou) {
                btn.classList.add('correta');
            } else {
                btn.classList.add('incorreta');
            }
        }
        
        // Marca a resposta correta
        if (perguntaData.opcoes[index] === data.resposta_correta) {
            btn.classList.add('resposta-correta');
            // Adiciona efeito de destaque se não foi a resposta do usuário
            if (index !== respostaSelecionada) {
                btn.classList.add('destaque-correta');
            }
        }
    });
    
    // Mostra feedback
    const feedbackContainer = document.getElementById('feedback-container');
    const feedbackClass = data.acertou ? 'feedback-correto' : 'feedback-incorreto';
    const feedbackIcon = data.acertou ? '✅' : '❌';
    const feedbackTexto = data.acertou ? 'Correto!' : 'Incorreto!';
    
    feedbackContainer.innerHTML = `
        <div class="feedback ${feedbackClass}">
            <div class="feedback-header">
                <span class="feedback-icon">${feedbackIcon}</span>
                <span class="feedback-texto">${feedbackTexto}</span>
            </div>
            ${!data.acertou ? `
                <div class="feedback-explicacao">
                    <strong>Resposta correta:</strong> ${data.resposta_correta}
                </div>
            ` : ''}
            <div class="feedback-pontos">
                Pontuação: ${data.pontos}/${perguntaAtual}
            </div>
            <div class="feedback-proximo">
                <span class="proximo-contador">Próxima pergunta em <span id="contador">3</span>s...</span>
            </div>
        </div>
    `;
    
    feedbackContainer.style.display = 'block';
    
    // AVANÇO AUTOMÁTICO após 3 segundos
    let contador = 3;
    const contadorElement = document.getElementById('contador');
    
    const interval = setInterval(() => {
        contador--;
        if (contadorElement) {
            contadorElement.textContent = contador;
        }
        
        if (contador <= 0) {
            clearInterval(interval);
            proximaPergunta();
        }
    }, 1000);
    
    // Permite pular o contador clicando em qualquer lugar
    document.addEventListener('click', function pularContador() {
        clearInterval(interval);
        document.removeEventListener('click', pularContador);
        proximaPergunta();
    }, { once: true });
    
    // Permite pular com qualquer tecla
    document.addEventListener('keydown', function pularContadorTecla(event) {
        clearInterval(interval);
        document.removeEventListener('keydown', pularContadorTecla);
        proximaPergunta();
    }, { once: true });
}

// Função para próxima pergunta
function proximaPergunta() {
    console.log('Carregando próxima pergunta...');
    carregarPergunta();
}

// Atalhos de teclado (APENAS PARA SELEÇÃO)
document.addEventListener('keydown', function(event) {
    // Se já respondeu, ignora (o avanço automático já cuida)
    if (respostaEnviada) return;
    
    // A, B, C, D para selecionar (e enviar automaticamente)
    const tecla = event.key.toLowerCase();
    if (tecla >= 'a' && tecla <= 'd') {
        const index = tecla.charCodeAt(0) - 97;
        const opcao = document.getElementById(`opcao-${index}`);
        if (opcao && !opcao.disabled) {
            event.preventDefault();
            selecionarResposta(index);
        }
    }
    
    // Números 1, 2, 3, 4 também funcionam
    if (tecla >= '1' && tecla <= '4') {
        const index = parseInt(tecla) - 1;
        const opcao = document.getElementById(`opcao-${index}`);
        if (opcao && !opcao.disabled) {
            event.preventDefault();
            selecionarResposta(index);
        }
    }
});

// Inicializa quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página carregada, iniciando quiz...');
    carregarPergunta();
});

function voltarInicio() {
    if (confirm('Tem certeza que deseja sair do quiz? Seu progresso será perdido e você verá o relatório.')) {
        window.location.href = '/finalizar_quiz';
    }
}

function tentarLerPerguntaEOpcoes() {
    let dadosUsuario = {};
    try {
        dadosUsuario = JSON.parse(localStorage.getItem('dadosUsuario')) || {};
    } catch(e) {}
    if (dadosUsuario.ler_perguntas) {
        if (typeof lerPerguntaEOpcoes === 'function') lerPerguntaEOpcoes();
    }
}