console.log('🚀 JavaScript carregado!');

// Variáveis globais
let currentQuestion = null;
let selectedAnswer = null;
let isAnswered = false;
let totalCorrect = 0;
let totalAnswered = 0;

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    console.log('📱 DOM carregado, iniciando quiz...');
    loadNextQuestion();
    startTimer();
});

// Carrega próxima pergunta
async function loadNextQuestion() {
    console.log('📥 Buscando próxima pergunta...');
    
    try {
        const response = await fetch('/proxima_pergunta');
        console.log('📡 Resposta recebida:', response.status);
        
        const data = await response.json();
        console.log('📊 Dados:', data);
        
        if (data.erro) {
            showError(data.erro);
            return;
        }
        
        if (data.tempo_esgotado) {
            window.location.href = '/finalizar_quiz';
            return;
        }
        
        if (data.fim) {
            window.location.href = '/resultado';
            return;
        }
        
        // Salva pergunta atual
        currentQuestion = data.pergunta;
        selectedAnswer = null;
        isAnswered = false;
        
        // Atualiza interface
        updateQuestionDisplay(data);
        updateStats(data.pontos);
        
        // Esconde botão próxima
        const nextBtn = document.getElementById('nextBtn');
        if (nextBtn) nextBtn.style.display = 'none';
        
    } catch (error) {
        console.error('❌ Erro:', error);
        showError('Erro ao carregar pergunta: ' + error.message);
    }
}

// Atualiza display da pergunta
function updateQuestionDisplay(data) {
    console.log('🖼️ Atualizando display da pergunta...');
    
    const questionArea = document.getElementById('questionArea');
    const pergunta = data.pergunta;
    
    // Atualiza números
    document.getElementById('questionNumber').textContent = data.numero;
    document.getElementById('totalQuestions').textContent = data.total;
    
    // Atualiza barra de progresso
    const progress = (data.numero / data.total) * 100;
    document.getElementById('progressBar').style.width = progress + '%';
    
    // Monta HTML da pergunta
    let optionsHTML = '';
    pergunta.opcoes.forEach((opcao, index) => {
        const letra = String.fromCharCode(65 + index); // A, B, C, D
        optionsHTML += `
            <button class="option-btn" onclick="selectOption('${letra}', this)" data-option="${letra}" style="width:100%;text-align:left;">
                <div class="option-letter">${letra}</div>
                <div class="option-text">${opcao}</div>
            </button>
        `;
    });
    
    const questionHTML = `
        <div class="question-card">
            <div class="question-text">
                ${pergunta.pergunta}
            </div>
            <div class="options-container" style="max-height:40vh;overflow-y:auto;margin-bottom:20px;padding-right:8px;">
                ${optionsHTML}
            </div>
            <div class="controls" style="position:sticky;bottom:0;background:rgba(255,255,255,0.95);padding:15px 0 0 0;z-index:2;display:flex;flex-wrap:wrap;gap:10px;justify-content:center;">
                <button type="button" class="btn secondary" onclick="voltarInicio()">
                    <i class="fas fa-home"></i>
                    Voltar ao Início
                </button>
                <button type="submit" class="btn primary" id="btn-responder">
                    <i class="fas fa-paper-plane"></i>
                    Responder
                </button>
            </div>
        </div>
    `;
    
    questionArea.innerHTML = questionHTML;
    console.log('✅ Pergunta exibida!');
}

// Seleciona uma opção
function selectOption(letter, buttonElement) {
    console.log('👆 Opção clicada:', letter);
    
    if (isAnswered) {
        console.log('⚠️ Já respondido, ignorando...');
        return;
    }
    
    // Remove seleção anterior
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // Adiciona seleção atual
    buttonElement.classList.add('selected');
    selectedAnswer = letter;
    
    console.log('✅ Opção selecionada:', letter);
    
    // Envia resposta após 1 segundo
    setTimeout(() => {
        if (selectedAnswer === letter && !isAnswered) {
            submitAnswer();
        }
    }, 1000);
}

// Envia resposta
async function submitAnswer() {
    if (!selectedAnswer || isAnswered) return;
    
    isAnswered = true;
    console.log('📤 Enviando resposta:', selectedAnswer);
    
    try {
        const response = await fetch('/responder', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                resposta: selectedAnswer,
                resposta_correta: currentQuestion.resposta_correta,
                opcoes: currentQuestion.opcoes
            })
        });
        
        const data = await response.json();
        console.log('📨 Resposta do servidor:', data);
        
        if (data.tempo_esgotado) {
            window.location.href = '/finalizar_quiz';
            return;
        }
        
        // Mostra resultado
        showAnswerResult(data);
        
        // Atualiza estatísticas
        totalAnswered++;
        if (data.correto) {
            totalCorrect++;
        }
        updateStats(data.pontos);
        
        // Mostra botão próxima após 2 segundos
        setTimeout(() => {
            const nextBtn = document.getElementById('nextBtn');
            if (nextBtn) nextBtn.style.display = 'block';
        }, 2000);
        
    } catch (error) {
        console.error('❌ Erro ao enviar resposta:', error);
        showError('Erro ao enviar resposta: ' + error.message);
        isAnswered = false;
    }
}

// Mostra resultado da resposta
function showAnswerResult(data) {
    console.log('🎯 Mostrando resultado:', data.correto ? 'CORRETO' : 'INCORRETO');
    
    const buttons = document.querySelectorAll('.option-btn');
    
    buttons.forEach(btn => {
        const option = btn.getAttribute('data-option');
        
        if (option === data.resposta_correta) {
            btn.classList.add('correct');
        } else if (option === selectedAnswer && !data.correto) {
            btn.classList.add('incorrect');
        }
        
        // Desabilita todos os botões
        btn.style.pointerEvents = 'none';
    });
    
    // Mostra feedback
    showFeedback(data.correto);
}

// Mostra feedback visual
function showFeedback(isCorrect) {
    const feedbackEl = document.getElementById('feedbackMessage');
    
    if (isCorrect) {
        feedbackEl.innerHTML = '<i class="fas fa-check-circle"></i> Correto!';
        feedbackEl.className = 'feedback-message correct';
    } else {
        feedbackEl.innerHTML = '<i class="fas fa-times-circle"></i> Incorreto!';
        feedbackEl.className = 'feedback-message incorrect';
    }
    
    feedbackEl.style.display = 'block';
    
    setTimeout(() => {
        feedbackEl.style.display = 'none';
    }, 2000);
}

// Atualiza estatísticas
function updateStats(points) {
    document.getElementById('currentPoints').textContent = points;
    document.getElementById('correctAnswers').textContent = totalCorrect;
    
    const accuracy = totalAnswered > 0 ? Math.round((totalCorrect / totalAnswered) * 100) : 0;
    document.getElementById('accuracy').textContent = accuracy + '%';
}

// Timer
function startTimer() {
    setInterval(updateTimer, 1000);
}

async function updateTimer() {
    try {
        const response = await fetch('/tempo_restante');
        const data = await response.json();
        
        if (data.tempo_esgotado) {
            window.location.href = '/finalizar_quiz';
            return;
        }
        
        const minutes = String(data.minutos).padStart(2, '0');
        const seconds = String(data.segundos).padStart(2, '0');
        document.getElementById('timeDisplay').textContent = `${minutes}:${seconds}`;
        
        // Aviso quando restam 2 minutos
        if (data.total_segundos <= 120) {
            document.getElementById('timer').classList.add('warning');
        }
        
    } catch (error) {
        console.error('❌ Erro no timer:', error);
    }
}

// Funções TTS (Text-to-Speech)
function readQuestion() {
    if (currentQuestion) {
        speak(currentQuestion.pergunta);
    }
}

function readAllOptions() {
    if (currentQuestion) {
        const text = currentQuestion.opcoes.map((opcao, index) => {
            const letra = String.fromCharCode(65 + index);
            return `Opção ${letra}: ${opcao}`;
        }).join('. ');
        speak(text);
    }
}

function speak(text) {
    stopReading();
    
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'pt-BR';
        utterance.rate = 0.9;
        utterance.pitch = 1;
        
        speechSynthesis.speak(utterance);
        showTTSStatus('Lendo...');
        
        utterance.onend = () => {
            hideTTSStatus();
        };
    } else {
        alert('Seu navegador não suporta síntese de voz.');
    }
}

function stopReading() {
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
        hideTTSStatus();
    }
}

function showTTSStatus(text) {
    const status = document.getElementById('ttsStatus');
    document.getElementById('ttsStatusText').textContent = text;
    status.classList.add('active');
}

function hideTTSStatus() {
    const status = document.getElementById('ttsStatus');
    status.classList.remove('active');
}

// Mostra erro
function showError(message) {
    console.error('🚨 Erro:', message);
    const questionArea = document.getElementById('questionArea');
    questionArea.innerHTML = `
        <div class="alert alert-danger text-center">
            <i class="fas fa-exclamation-triangle"></i>
            <h5>Erro</h5>
            <p>${message}</p>
            <button class="btn btn-primary" onclick="window.location.href='/'">
                <i class="fas fa-home"></i> Voltar ao Início
            </button>
        </div>
    `;
}

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