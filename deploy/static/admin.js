// ========================================
// ADMIN PANEL - FUNCIONALIDADES COMPLETAS
// ========================================

let perguntasCarregadas = {};
let uploadCancelado = false;

// ========================================
// FUNÇÕES DE NAVEGAÇÃO
// ========================================

function mostrarTab(tabName) {
    // Remove classe active de todas as tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Adiciona classe active na tab selecionada
    document.querySelector(`[onclick="mostrarTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    // Carrega dados específicos da tab
    switch(tabName) {
        case 'listar':
            carregarDisciplinas();
            break;
        case 'estatisticas':
            carregarEstatisticas();
            break;
    }
}

// ========================================
// FUNÇÕES DO FORMULÁRIO DE ADIÇÃO
// ========================================

function adicionarOpcao() {
    const lista = document.getElementById('opcoes-lista');
    const opcoes = lista.children;
    
    if (opcoes.length >= 5) {
        mostrarAlerta('Máximo de 5 opções permitidas.', 'error');
        return;
    }
    
    const novaOpcao = document.createElement('div');
    novaOpcao.className = 'opcao-item';
    novaOpcao.innerHTML = `
        <input type="text" placeholder="Opção ${opcoes.length + 1}" required>
        <button type="button" onclick="removerOpcao(this)">❌</button>
    `;
    
    lista.appendChild(novaOpcao);
    atualizarSelectResposta();
    atualizarBotaoAdicionar();
}

function removerOpcao(button) {
    const opcaoItem = button.parentElement;
    const lista = document.getElementById('opcoes-lista');
    
    if (lista.children.length <= 4) {
        mostrarAlerta('Mínimo de 4 opções obrigatórias.', 'error');
        return;
    }
    
    opcaoItem.remove();
    atualizarSelectResposta();
    atualizarBotaoAdicionar();
}

function atualizarSelectResposta() {
    const select = document.getElementById('resposta-correta');
    const opcoes = document.querySelectorAll('#opcoes-lista input');
    
    select.innerHTML = '<option value="">Selecione a resposta correta</option>';
    
    opcoes.forEach((input, index) => {
        if (input.value.trim()) {
            const option = document.createElement('option');
            option.value = input.value.trim();
            option.textContent = `Opção ${index + 1}: ${input.value.trim()}`;
            select.appendChild(option);
        }
    });
}

function atualizarBotaoAdicionar() {
    const lista = document.getElementById('opcoes-lista');
    const btn = document.getElementById('btn-adicionar-opcao');
    
    if (lista.children.length >= 5) {
        btn.disabled = true;
        btn.textContent = 'Máximo de 5 opções atingido';
    } else {
        btn.disabled = false;
        btn.textContent = `➕ Adicionar Opção (${lista.children.length}/5)`;
    }
}

// ========================================
// FUNÇÕES DE SUBMISSÃO
// ========================================

document.getElementById('form-pergunta').addEventListener('submit', function(e) {
    e.preventDefault();
    salvarPergunta();
});

function salvarPergunta() {
    const form = document.getElementById('form-pergunta');
    const formData = new FormData(form);
    
    // Coleta dados do formulário
    const dados = {
        disciplina: formData.get('disciplina').trim(),
        topico: formData.get('topico').trim(),
        pergunta: formData.get('pergunta').trim(),
        opcoes: [],
        resposta_correta: formData.get('resposta-correta').trim(),
        categoria: formData.get('categoria').trim(),
        dificuldade: formData.get('dificuldade'),
        explicacao: formData.get('explicacao').trim(),
        referencia: formData.get('referencia').trim()
    };
    
    // Coleta opções
    const opcoesInputs = document.querySelectorAll('#opcoes-lista input');
    opcoesInputs.forEach(input => {
        if (input.value.trim()) {
            dados.opcoes.push(input.value.trim());
        }
    });
    
    // Validações
    if (!dados.disciplina || !dados.topico || !dados.pergunta) {
        mostrarAlerta('Preencha todos os campos obrigatórios.', 'error');
        return;
    }
    
    if (dados.opcoes.length < 4) {
        mostrarAlerta('Mínimo de 4 opções obrigatórias.', 'error');
        return;
    }
    
    if (!dados.resposta_correta) {
        mostrarAlerta('Selecione a resposta correta.', 'error');
        return;
    }
    
    // Mostra loading
    const btnSubmit = document.querySelector('#form-pergunta button[type="submit"]');
    const textoOriginal = btnSubmit.innerHTML;
    btnSubmit.innerHTML = '⏳ Salvando...';
    btnSubmit.disabled = true;
    
    // Envia para o servidor
    fetch('/admin/adicionar-pergunta', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            limparFormulario();
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao salvar pergunta.', 'error');
    })
    .finally(() => {
        btnSubmit.innerHTML = textoOriginal;
        btnSubmit.disabled = false;
    });
}

function limparFormulario() {
    document.getElementById('form-pergunta').reset();
    
    // Reseta opções para 4 padrão
    const lista = document.getElementById('opcoes-lista');
    lista.innerHTML = `
        <div class="opcao-item">
            <input type="text" placeholder="Opção 1" required>
            <button type="button" onclick="removerOpcao(this)" disabled>❌</button>
        </div>
        <div class="opcao-item">
            <input type="text" placeholder="Opção 2" required>
            <button type="button" onclick="removerOpcao(this)" disabled>❌</button>
        </div>
        <div class="opcao-item">
            <input type="text" placeholder="Opção 3" required>
            <button type="button" onclick="removerOpcao(this)" disabled>❌</button>
        </div>
        <div class="opcao-item">
            <input type="text" placeholder="Opção 4" required>
            <button type="button" onclick="removerOpcao(this)" disabled>❌</button>
        </div>
    `;
    
    atualizarSelectResposta();
    atualizarBotaoAdicionar();
}

// ========================================
// FUNÇÕES DE LISTAGEM E GERENCIAMENTO
// ========================================

function carregarDisciplinas() {
    const select = document.getElementById('filtro-disciplina');
    if (select.children.length <= 1) {
        // Carrega disciplinas dinamicamente se necessário
        fetch('/admin/listar-disciplinas')
            .then(response => response.json())
            .then(data => {
                if (data.disciplinas) {
                    data.disciplinas.forEach(disciplina => {
                        const option = document.createElement('option');
                        option.value = disciplina;
                        option.textContent = disciplina;
                        select.appendChild(option);
                    });
                }
            })
            .catch(error => console.error('Erro ao carregar disciplinas:', error));
    }
}

function carregarTopicos() {
    const disciplina = document.getElementById('filtro-disciplina').value;
    const selectTopico = document.getElementById('filtro-topico');
    
    // Limpa tópicos
    selectTopico.innerHTML = '<option value="">Todos os tópicos</option>';
    
    if (!disciplina) {
        document.getElementById('lista-perguntas').innerHTML = `
            <p style="text-align: center; color: #6c757d; padding: 40px;">
                Selecione uma disciplina para visualizar as perguntas
            </p>
        `;
        return;
    }
    
    // Mostra loading
    document.getElementById('lista-perguntas').innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div style="color: #007bff; font-size: 24px; margin-bottom: 10px;">⏳</div>
            <p>Carregando perguntas...</p>
        </div>
    `;
    
    // Carrega tópicos da disciplina
    fetch(`/admin/listar-topicos/${encodeURIComponent(disciplina)}`)
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                mostrarAlerta('Erro: ' + data.erro, 'error');
                return;
            }
            
            perguntasCarregadas = data;
            
            // Popula select de tópicos
            Object.keys(data).forEach(topico => {
                const option = document.createElement('option');
                option.value = topico;
                option.textContent = `${topico} (${data[topico].total_perguntas} perguntas)`;
                selectTopico.appendChild(option);
            });
            
            // Carrega todas as perguntas da disciplina
            carregarPerguntas();
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarAlerta('Erro ao carregar tópicos.', 'error');
        });
}

function carregarPerguntas() {
    const disciplina = document.getElementById('filtro-disciplina').value;
    const topico = document.getElementById('filtro-topico').value;
    const container = document.getElementById('lista-perguntas');
    
    if (!disciplina) {
        container.innerHTML = `
            <p style="text-align: center; color: #6c757d; padding: 40px;">
                Selecione uma disciplina para visualizar as perguntas
            </p>
        `;
        return;
    }
    
    let html = '';
    let totalPerguntas = 0;
    
    // Filtra por tópico se selecionado
    const topicosParaMostrar = topico ? [topico] : Object.keys(perguntasCarregadas);
    
    topicosParaMostrar.forEach(nomeTopico => {
        if (!perguntasCarregadas[nomeTopico]) return;
        
        const dadosTopico = perguntasCarregadas[nomeTopico];
        const perguntas = dadosTopico.perguntas;
        
        html += `
            <div class="disciplina-item">
                <h4>🎯 ${nomeTopico} (${perguntas.length} perguntas)</h4>
        `;
        
        perguntas.forEach((pergunta, index) => {
            totalPerguntas++;
            const dificuldadeIcon = pergunta.dificuldade === 'facil' ? '😊' : 
                                  pergunta.dificuldade === 'dificil' ? '😰' : '😐';
            
            html += `
                <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin: 15px 0;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                        <div style="flex: 1;">
                            <h5 style="color: #495057; margin-bottom: 10px;">
                                ❓ Pergunta ${index + 1} ${dificuldadeIcon}
                            </h5>
                            <p style="font-weight: 500; margin-bottom: 15px;">${pergunta.pergunta}</p>
                        </div>
                        <div style="display: flex; gap: 10px;">
                            <button class="btn primary" onclick="editarPergunta('${disciplina}', '${nomeTopico}', ${index})">
                                ✏️ Editar
                            </button>
                            <button class="btn danger" onclick="excluirPergunta('${disciplina}', '${nomeTopico}', ${index})">
                                🗑️ Excluir
                            </button>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <strong>📝 Opções:</strong>
                        <ol style="margin: 10px 0; padding-left: 20px;">
            `;
            
            pergunta.opcoes.forEach(opcao => {
                const isCorreta = opcao === pergunta.resposta_correta;
                html += `
                    <li style="margin: 5px 0; ${isCorreta ? 'color: #28a745; font-weight: bold;' : ''} ">
                        ${opcao} ${isCorreta ? '✅' : ''}
                    </li>
                `;
            });
            
            html += `
                        </ol>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 14px; color: #6c757d;">
                        <div><strong>🏷️ Categoria:</strong> ${pergunta.categoria || 'N/A'}</div>
                        <div><strong>⭐ Dificuldade:</strong> ${pergunta.dificuldade || 'medio'}</div>
                    </div>
            `;
            
            if (pergunta.explicacao) {
                html += `
                    <div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <strong>💡 Explicação:</strong> ${pergunta.explicacao}
                    </div>
                `;
            }
            
            if (pergunta.referencia) {
                html += `
                    <div style="margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px;">
                        <strong>📖 Referência:</strong> ${pergunta.referencia}
                    </div>
                `;
            }
            
            html += `
                </div>
            `;
        });
        
        html += `</div>`;
    });
    
    if (totalPerguntas === 0) {
        html = `
            <p style="text-align: center; color: #6c757d; padding: 40px;">
                Nenhuma pergunta encontrada para os filtros selecionados
            </p>
        `;
    }
    
    container.innerHTML = html;
}

// ========================================
// FUNÇÕES DE EDIÇÃO E EXCLUSÃO
// ========================================

function editarPergunta(disciplina, topico, indice) {
    // Carrega dados da pergunta
    fetch(`/admin/obter-pergunta/${encodeURIComponent(disciplina)}/${encodeURIComponent(topico)}/${indice}`)
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                mostrarAlerta('Erro: ' + data.erro, 'error');
                return;
            }
            
            const pergunta = data.pergunta;
            
            // Preenche formulário
            document.getElementById('disciplina').value = pergunta.disciplina;
            document.getElementById('topico').value = pergunta.topico;
            document.getElementById('pergunta').value = pergunta.pergunta;
            document.getElementById('categoria').value = pergunta.categoria || '';
            document.getElementById('dificuldade').value = pergunta.dificuldade || 'medio';
            document.getElementById('explicacao').value = pergunta.explicacao || '';
            document.getElementById('referencia').value = pergunta.referencia || '';
            
            // Preenche opções
            const lista = document.getElementById('opcoes-lista');
            lista.innerHTML = '';
            
            pergunta.opcoes.forEach((opcao, index) => {
                const opcaoItem = document.createElement('div');
                opcaoItem.className = 'opcao-item';
                opcaoItem.innerHTML = `
                    <input type="text" value="${opcao}" placeholder="Opção ${index + 1}" required>
                    <button type="button" onclick="removerOpcao(this)" ${index < 4 ? 'disabled' : ''}>❌</button>
                `;
                lista.appendChild(opcaoItem);
            });
            
            atualizarSelectResposta();
            atualizarBotaoAdicionar();
            
            // Define resposta correta
            document.getElementById('resposta-correta').value = pergunta.resposta_correta;
            
            // Muda para tab de adicionar
            mostrarTab('adicionar');
            
            // Adiciona botão de atualizar
            const btnSubmit = document.querySelector('#form-pergunta button[type="submit"]');
            btnSubmit.innerHTML = '💾 Atualizar Pergunta';
            btnSubmit.onclick = function(e) {
                e.preventDefault();
                atualizarPergunta(disciplina, topico, indice);
            };
            
            mostrarAlerta('Pergunta carregada para edição. Clique em "Atualizar Pergunta" para salvar as mudanças.', 'info');
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarAlerta('Erro ao carregar pergunta para edição.', 'error');
        });
}

function atualizarPergunta(disciplina, topico, indice) {
    const form = document.getElementById('form-pergunta');
    const formData = new FormData(form);
    
    // Coleta dados do formulário
    const dados = {
        disciplina: formData.get('disciplina').trim(),
        topico: formData.get('topico').trim(),
        pergunta: formData.get('pergunta').trim(),
        opcoes: [],
        resposta_correta: formData.get('resposta-correta').trim(),
        categoria: formData.get('categoria').trim(),
        dificuldade: formData.get('dificuldade'),
        explicacao: formData.get('explicacao').trim(),
        referencia: formData.get('referencia').trim(),
        indice: indice
    };
    
    // Coleta opções
    const opcoesInputs = document.querySelectorAll('#opcoes-lista input');
    opcoesInputs.forEach(input => {
        if (input.value.trim()) {
            dados.opcoes.push(input.value.trim());
        }
    });
    
    // Validações
    if (!dados.disciplina || !dados.topico || !dados.pergunta) {
        mostrarAlerta('Preencha todos os campos obrigatórios.', 'error');
        return;
    }
    
    if (dados.opcoes.length < 4) {
        mostrarAlerta('Mínimo de 4 opções obrigatórias.', 'error');
        return;
    }
    
    if (!dados.resposta_correta) {
        mostrarAlerta('Selecione a resposta correta.', 'error');
        return;
    }
    
    // Mostra loading
    const btnSubmit = document.querySelector('#form-pergunta button[type="submit"]');
    const textoOriginal = btnSubmit.innerHTML;
    btnSubmit.innerHTML = '⏳ Atualizando...';
    btnSubmit.disabled = true;
    
    // Envia para o servidor
    fetch('/admin/editar-pergunta', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            limparFormulario();
            
            // Restaura botão original
            btnSubmit.innerHTML = '💾 Salvar Pergunta';
            btnSubmit.onclick = null;
            
            // Recarrega perguntas se estiver na tab de listar
            if (document.getElementById('tab-listar').classList.contains('active')) {
                carregarPerguntas();
            }
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao atualizar pergunta.', 'error');
    })
    .finally(() => {
        btnSubmit.innerHTML = textoOriginal;
        btnSubmit.disabled = false;
    });
}

function excluirPergunta(disciplina, topico, indice) {
    if (!confirm('Tem certeza que deseja excluir esta pergunta? Esta ação não pode ser desfeita.')) {
        return;
    }
    
    fetch('/admin/excluir-pergunta', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            disciplina: disciplina,
            topico: topico,
            indice: indice
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            carregarPerguntas(); // Recarrega a lista
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao excluir pergunta.', 'error');
    });
}

// ========================================
// FUNÇÕES DE UPLOAD
// ========================================

function arquivoSelecionado() {
    const input = document.getElementById('arquivo-upload');
    const file = input.files[0];
    
    if (!file) return;
    
    if (!file.name.endsWith('.json')) {
        mostrarAlerta('Selecione apenas arquivos JSON.', 'error');
        return;
    }
    
    // Mostra área de progresso
    document.getElementById('upload-area').style.display = 'none';
    document.getElementById('upload-progress').style.display = 'block';
    
    // Reseta contadores
    document.getElementById('count-success').textContent = '0';
    document.getElementById('count-errors').textContent = '0';
    document.getElementById('count-total').textContent = '0';
    
    uploadCancelado = false;
    
    // Simula progresso
    let progress = 0;
    const progressBar = document.getElementById('progress-bar-upload');
    const progressText = document.getElementById('progress-text');
    const progressPercent = document.getElementById('progress-percent');
    
    const progressInterval = setInterval(() => {
        if (uploadCancelado) {
            clearInterval(progressInterval);
            return;
        }
        
        progress += Math.random() * 10;
        if (progress > 90) progress = 90;
        
        progressBar.style.width = progress + '%';
        progressPercent.textContent = Math.round(progress) + '%';
        progressText.textContent = 'Processando arquivo...';
    }, 200);
    
    // Lê e envia arquivo
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = JSON.parse(e.target.result);
            
            // Cria FormData
            const formData = new FormData();
            formData.append('file', file);
            
            // Envia para servidor
            fetch('/admin/upload-perguntas', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(result => {
                clearInterval(progressInterval);
                
                if (result.sucesso) {
                    progressBar.style.width = '100%';
                    progressPercent.textContent = '100%';
                    progressText.textContent = 'Upload concluído!';
                    
                    setTimeout(() => {
                        mostrarResultadoUpload(result);
                    }, 500);
                } else {
                    mostrarAlerta('Erro: ' + (result.erro || 'Erro desconhecido'), 'error');
                    resetarUpload();
                }
            })
            .catch(error => {
                clearInterval(progressInterval);
                console.error('Erro:', error);
                mostrarAlerta('Erro ao fazer upload.', 'error');
                resetarUpload();
            });
            
        } catch (error) {
            clearInterval(progressInterval);
            mostrarAlerta('Arquivo JSON inválido.', 'error');
            resetarUpload();
        }
    };
    
    reader.readAsText(file);
}

function cancelarUpload() {
    uploadCancelado = true;
    resetarUpload();
    mostrarAlerta('Upload cancelado.', 'info');
}

function resetarUpload() {
    document.getElementById('upload-area').style.display = 'block';
    document.getElementById('upload-progress').style.display = 'none';
    document.getElementById('upload-result').style.display = 'none';
    document.getElementById('arquivo-upload').value = '';
}

function mostrarResultadoUpload(result) {
    const container = document.getElementById('upload-result');
    const content = document.getElementById('result-content');
    
    content.innerHTML = `
        <div class="alert success">
            <h4>✅ Upload Concluído!</h4>
            <p><strong>${result.mensagem}</strong></p>
            <p>Total de perguntas importadas: <strong>${result.total_perguntas}</strong></p>
        </div>
    `;
    
    container.style.display = 'block';
    
    // Atualiza contadores
    document.getElementById('count-success').textContent = result.total_perguntas;
    document.getElementById('count-total').textContent = result.total_perguntas;
    
    setTimeout(() => {
        resetarUpload();
    }, 5000);
}

function baixarExemplo() {
    fetch('/admin/exemplo-json')
        .then(response => response.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'exemplo_perguntas.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Erro:', error);
            mostrarAlerta('Erro ao baixar exemplo.', 'error');
        });
}

// ========================================
// FUNÇÕES DE ESTATÍSTICAS
// ========================================

function carregarEstatisticas() {
    // As estatísticas já são carregadas pelo template
    // Esta função pode ser usada para atualizações dinâmicas
}

// ========================================
// FUNÇÕES UTILITÁRIAS
// ========================================

function mostrarAlerta(mensagem, tipo) {
    const alertContainer = document.getElementById('alert-container');
    const alert = document.createElement('div');
    alert.className = `alert ${tipo}`;
    alert.textContent = mensagem;
    
    alertContainer.appendChild(alert);
    
    // Remove após 5 segundos
    setTimeout(() => {
        alert.remove();
    }, 5000);
}

// ========================================
// FUNÇÕES DE GERENCIAMENTO DE DISCIPLINAS
// ========================================

// Event listener para o select de disciplina
document.addEventListener('DOMContentLoaded', function() {
    const selectDisciplina = document.getElementById('disciplina-remover');
    if (selectDisciplina) {
        selectDisciplina.addEventListener('change', function() {
            const disciplina = this.value;
            const btnRemover = document.getElementById('btn-remover-disciplina');
            const infoDiv = document.getElementById('info-disciplina');
            
            if (disciplina) {
                btnRemover.disabled = false;
                carregarInfoDisciplina(disciplina);
                infoDiv.style.display = 'block';
            } else {
                btnRemover.disabled = true;
                infoDiv.style.display = 'none';
            }
        });
    }
});

function carregarInfoDisciplina(disciplina) {
    const infoContent = document.getElementById('info-disciplina-content');
    
    // Mostra loading
    infoContent.innerHTML = '<div style="text-align: center; color: #007bff;">⏳ Carregando informações...</div>';
    
    // Busca informações da disciplina
    fetch(`/admin/listar-topicos/${encodeURIComponent(disciplina)}`)
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                infoContent.innerHTML = `<div style="color: #dc3545;">❌ Erro: ${data.erro}</div>`;
                return;
            }
            
            let totalPerguntas = 0;
            let topicos = [];
            
            Object.keys(data).forEach(topico => {
                const perguntas = data[topico].total_perguntas;
                totalPerguntas += perguntas;
                topicos.push(`${topico} (${perguntas} perguntas)`);
            });
            
            infoContent.innerHTML = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
                    <div><strong>📚 Disciplina:</strong> ${disciplina}</div>
                    <div><strong>🎯 Total de Tópicos:</strong> ${Object.keys(data).length}</div>
                    <div><strong>❓ Total de Perguntas:</strong> ${totalPerguntas}</div>
                </div>
                
                <h6 style="color: #495057; margin-bottom: 10px;">📋 Tópicos que serão removidos:</h6>
                ${topicos.map(topico => `<div class="topico-item">${topico}</div>`).join('')}
                
                <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; color: #856404;">
                    <strong>⚠️ Atenção:</strong> Esta ação criará um backup automático antes da remoção, mas é irreversível.
        </div>
    `;
        })
        .catch(error => {
            console.error('Erro:', error);
            infoContent.innerHTML = '<div style="color: #dc3545;">❌ Erro ao carregar informações da disciplina</div>';
        });
}

function removerDisciplina() {
    const disciplina = document.getElementById('disciplina-remover').value;
    
    if (!disciplina) {
        mostrarAlerta('Selecione uma disciplina para remover.', 'error');
        return;
    }
    
    if (!confirm(`Tem certeza que deseja remover a disciplina "${disciplina}"?\n\nEsta ação criará um backup automático, mas é irreversível.`)) {
        return;
    }
    
    // Mostra loading
    const btnRemover = document.getElementById('btn-remover-disciplina');
    const textoOriginal = btnRemover.innerHTML;
    btnRemover.innerHTML = '⏳ Removendo...';
    btnRemover.disabled = true;
    
    fetch('/admin/remover-disciplina', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ disciplina: disciplina })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            document.getElementById('disciplina-remover').value = '';
            document.getElementById('btn-remover-disciplina').disabled = true;
            document.getElementById('info-disciplina').style.display = 'none';
            
            // Recarrega disciplinas disponíveis
            carregarDisciplinas();
            
            // Atualiza estatísticas
            carregarEstatisticas();
            
            // Mostra detalhes da remoção
    setTimeout(() => {
                mostrarAlerta(`✅ Backup criado: ${data.backup_criado}\n📊 ${data.total_perguntas_removidas} perguntas removidas de ${data.total_topicos_removidos} tópicos`, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao remover disciplina.', 'error');
    })
    .finally(() => {
        btnRemover.innerHTML = textoOriginal;
        btnRemover.disabled = false;
    });
}

// ========================================
// FUNÇÕES DE GERENCIAMENTO DE BACKUPS
// ========================================

function carregarBackups() {
    const listaBackups = document.getElementById('lista-backups');
    
    // Mostra loading
    listaBackups.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div style="color: #007bff; font-size: 24px; margin-bottom: 10px;">⏳</div>
            <p>Carregando backups...</p>
        </div>
    `;
    
    fetch('/admin/listar-backups')
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                listaBackups.innerHTML = `<div style="color: #dc3545; text-align: center; padding: 40px;">❌ Erro: ${data.erro}</div>`;
                return;
            }
            
            if (data.backups.length === 0) {
                listaBackups.innerHTML = `
                    <div style="text-align: center; color: #6c757d; padding: 40px;">
                        <div style="font-size: 48px; color: #ccc; margin-bottom: 20px;">💾</div>
                        <h4>Nenhum backup encontrado</h4>
                        <p>Os backups aparecerão aqui quando você remover disciplinas.</p>
                    </div>
                `;
                atualizarEstatisticasBackups(data.backups);
                return;
            }
            
            // Renderiza lista de backups
            listaBackups.innerHTML = data.backups.map(backup => `
                <div class="disciplina-item">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                        <div>
                            <h4>📚 ${backup.disciplina}</h4>
                            <p style="color: #666; margin: 5px 0;">📅 Criado em: ${backup.data_criacao}</p>
                            <p style="color: #666; margin: 5px 0;">📁 Arquivo: ${backup.filename}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.2em; font-weight: bold; color: #007bff;">${backup.total_perguntas}</div>
                            <div style="color: #666; font-size: 0.9em;">perguntas</div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button class="btn primary" onclick="restaurarBackup('${backup.filename}')">
                            🔄 Restaurar
                        </button>
                        <button class="btn danger" onclick="excluirBackup('${backup.filename}')">
                            🗑️ Excluir Backup
                        </button>
                    </div>
                </div>
            `).join('');
            
            atualizarEstatisticasBackups(data.backups);
        })
        .catch(error => {
            console.error('Erro:', error);
            listaBackups.innerHTML = '<div style="color: #dc3545; text-align: center; padding: 40px;">❌ Erro ao carregar backups</div>';
        });
}

function restaurarBackup(filename) {
    if (!confirm(`Tem certeza que deseja restaurar este backup?\n\nArquivo: ${filename}\n\nSe a disciplina já existir, ela será substituída.`)) {
        return;
    }
    
    fetch('/admin/restaurar-backup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            carregarDisciplinas();
            carregarBackups();
            carregarEstatisticas();
            
            // Mostra detalhes da restauração
            setTimeout(() => {
                const msg = data.disciplina_existente_substituida 
                    ? `⚠️ Disciplina existente foi substituída.\n📊 ${data.total_perguntas_restauradas} perguntas restauradas de ${data.total_topicos_restaurados} tópicos`
                    : `📊 ${data.total_perguntas_restauradas} perguntas restauradas de ${data.total_topicos_restaurados} tópicos`;
                mostrarAlerta(msg, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao restaurar backup.', 'error');
    });
}

function excluirBackup(filename) {
    if (!confirm(`Tem certeza que deseja excluir este backup?\n\nArquivo: ${filename}\n\nEsta ação é irreversível.`)) {
        return;
    }
    
    fetch('/admin/excluir-backup', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            carregarBackups(); // Recarrega a lista
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao excluir backup.', 'error');
    });
}

function atualizarEstatisticasBackups(backups) {
    document.getElementById('total-backups').textContent = backups.length;
    
    // Conta disciplinas únicas
    const disciplinasUnicas = new Set(backups.map(b => b.disciplina));
    document.getElementById('disciplinas-backup').textContent = disciplinasUnicas.size;
    
    // Soma total de perguntas
    const totalPerguntas = backups.reduce((sum, backup) => sum + backup.total_perguntas, 0);
    document.getElementById('total-perguntas-backup').textContent = totalPerguntas;
    
    // Habilita/desabilita botões de ação em massa
    const btnRestaurarTodos = document.getElementById('btn-restaurar-todos');
    const btnLimparTodos = document.getElementById('btn-limpar-todos');
    
    if (backups.length > 0) {
        btnRestaurarTodos.disabled = false;
        btnLimparTodos.disabled = false;
    } else {
        btnRestaurarTodos.disabled = true;
        btnLimparTodos.disabled = true;
    }
}

function restaurarTodosBackups() {
    if (!confirm(`Tem certeza que deseja restaurar TODOS os backups?\n\n⚠️ ATENÇÃO:\n- Esta ação criará um backup do estado atual\n- Todas as disciplinas em backup serão restauradas\n- Disciplinas existentes serão substituídas\n- Esta ação pode demorar alguns segundos\n\nDeseja continuar?`)) {
        return;
    }
    
    // Mostra loading
    const btnRestaurar = document.getElementById('btn-restaurar-todos');
    const textoOriginal = btnRestaurar.innerHTML;
    btnRestaurar.innerHTML = '⏳ Restaurando...';
    btnRestaurar.disabled = true;
    
    fetch('/admin/restaurar-todos-backups', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            carregarDisciplinas();
            carregarBackups();
            carregarEstatisticas();
            
            // Mostra detalhes da restauração
            setTimeout(() => {
                let msg = `✅ Restauração completa realizada!\n\n`;
                msg += `📊 ${data.total_backups_restaurados} backups restaurados\n`;
                msg += `❓ ${data.total_perguntas_restauradas} perguntas restauradas\n`;
                msg += `🎯 ${data.total_topicos_restaurados} tópicos restaurados\n\n`;
                
                if (data.disciplinas_restauradas.length > 0) {
                    msg += `📚 Disciplinas restauradas: ${data.disciplinas_restauradas.join(', ')}\n`;
                }
                
                if (data.disciplinas_substituidas.length > 0) {
                    msg += `⚠️ Disciplinas substituídas: ${data.disciplinas_substituidas.join(', ')}\n`;
                }
                
                msg += `\n💾 Backup do estado atual: ${data.backup_estado_atual}`;
                
                mostrarAlerta(msg, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao restaurar todos os backups.', 'error');
    })
    .finally(() => {
        btnRestaurar.innerHTML = textoOriginal;
        btnRestaurar.disabled = false;
    });
}

function limparTodosBackups() {
    if (!confirm(`Tem certeza que deseja excluir TODOS os backups?\n\n⚠️ ATENÇÃO:\n- Esta ação criará um backup do estado atual\n- TODOS os arquivos de backup serão removidos permanentemente\n- Esta ação é irreversível\n- Você não poderá restaurar as disciplinas removidas\n\nDeseja continuar?`)) {
        return;
    }
    
    // Mostra loading
    const btnLimpar = document.getElementById('btn-limpar-todos');
    const textoOriginal = btnLimpar.innerHTML;
    btnLimpar.innerHTML = '⏳ Limpando...';
    btnLimpar.disabled = true;
    
    fetch('/admin/limpar-todos-backups', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            carregarBackups();
            carregarEstatisticas();
            
            // Mostra detalhes da limpeza
            setTimeout(() => {
                let msg = `✅ Limpeza de backups realizada!\n\n`;
                msg += `🗑️ ${data.total_backups_removidos} backups removidos\n`;
                msg += `💾 Backup do estado atual: ${data.backup_estado_atual}\n\n`;
                msg += `📁 Arquivos removidos:\n`;
                data.arquivos_removidos.forEach(arquivo => {
                    msg += `  - ${arquivo}\n`;
                });
                
                mostrarAlerta(msg, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao limpar todos os backups.', 'error');
    })
    .finally(() => {
        btnLimpar.innerHTML = textoOriginal;
        btnLimpar.disabled = false;
    });
}

// ========================================
// FUNÇÕES DE GERENCIAMENTO DO QUIZ PRINCIPAL
// ========================================

// Event listener para o select de disciplina do quiz principal
document.addEventListener('DOMContentLoaded', function() {
    const selectDisciplinaPrincipal = document.getElementById('disciplina-principal-remover');
    if (selectDisciplinaPrincipal) {
        // Carrega disciplinas disponíveis
        carregarDisciplinasPrincipais();
    }
});

function carregarDisciplinasPrincipais() {
    const selectDisciplina = document.getElementById('disciplina-principal-remover');
    if (!selectDisciplina) return;
    
    // Busca disciplinas do quiz principal
    fetch('/admin/listar-perguntas-principais')
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                console.error('Erro ao carregar disciplinas:', data.erro);
                return;
            }
            
            // Extrai disciplinas únicas
            const disciplinas = [...new Set(data.perguntas.map(p => p.disciplina))].sort();
            
            // Limpa e popula o select
            selectDisciplina.innerHTML = '<option value="">Escolha uma disciplina...</option>';
            disciplinas.forEach(disciplina => {
                const option = document.createElement('option');
                option.value = disciplina;
                option.textContent = disciplina;
                selectDisciplina.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Erro:', error);
        });
}

function carregarPeriodos() {
    const selectDisciplina = document.getElementById('disciplina-principal-remover');
    const selectPeriodo = document.getElementById('periodo-principal-remover');
    const disciplina = selectDisciplina.value;
    
    if (!disciplina) {
        selectPeriodo.innerHTML = '<option value="">Toda a disciplina</option>';
        return;
    }
    
    // Busca períodos da disciplina
    fetch(`/admin/listar-perguntas-principais?disciplina=${encodeURIComponent(disciplina)}`)
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                console.error('Erro ao carregar períodos:', data.erro);
                return;
            }
            
            // Extrai períodos únicos
            const periodos = [...new Set(data.perguntas.map(p => p.periodo))].sort((a, b) => a - b);
            
            // Limpa e popula o select
            selectPeriodo.innerHTML = '<option value="">Toda a disciplina</option>';
            periodos.forEach(periodo => {
                const option = document.createElement('option');
                option.value = periodo;
                option.textContent = `Período ${periodo}`;
                selectPeriodo.appendChild(option);
            });
            
            // Carrega informações da disciplina
            carregarInfoDisciplinaPrincipal();
        })
        .catch(error => {
            console.error('Erro:', error);
        });
}

function carregarInfoDisciplinaPrincipal() {
    const disciplina = document.getElementById('disciplina-principal-remover').value;
    const periodo = document.getElementById('periodo-principal-remover').value;
    const infoContent = document.getElementById('info-disciplina-principal-content');
    const infoDiv = document.getElementById('info-disciplina-principal');
    const btnRemover = document.getElementById('btn-remover-disciplina-principal');
    
    if (!disciplina) {
        btnRemover.disabled = true;
        infoDiv.style.display = 'none';
        return;
    }
    
    // Mostra loading
    infoContent.innerHTML = '<div style="text-align: center; color: #007bff;">⏳ Carregando informações...</div>';
    infoDiv.style.display = 'block';
    
    // Busca informações da disciplina
    let url = `/admin/listar-perguntas-principais?disciplina=${encodeURIComponent(disciplina)}`;
    if (periodo) {
        url += `&periodo=${periodo}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                infoContent.innerHTML = `<div style="color: #dc3545;">❌ Erro: ${data.erro}</div>`;
                return;
            }
            
            const perguntas = data.perguntas;
            const totalPerguntas = perguntas.length;
            
            // Agrupa por período se não foi especificado um período
            let periodos = {};
            if (!periodo) {
                perguntas.forEach(p => {
                    const p_periodo = p.periodo;
                    if (!periodos[p_periodo]) periodos[p_periodo] = 0;
                    periodos[p_periodo]++;
                });
            }
            
            let html = `
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
                    <div><strong>📚 Disciplina:</strong> ${disciplina}</div>
                    <div><strong>❓ Total de Perguntas:</strong> ${totalPerguntas}</div>
            `;
            
            if (periodo) {
                html += `<div><strong>📅 Período:</strong> ${periodo}</div>`;
            } else {
                html += `<div><strong>📅 Períodos:</strong> ${Object.keys(periodos).length}</div>`;
            }
            
            html += `</div>`;
            
            if (!periodo && Object.keys(periodos).length > 0) {
                html += `<h6 style="color: #495057; margin-bottom: 10px;">📋 Períodos que serão removidos:</h6>`;
                Object.keys(periodos).sort((a, b) => a - b).forEach(p => {
                    html += `<div class="topico-item">Período ${p} (${periodos[p]} perguntas)</div>`;
                });
            }
            
            html += `
                <div style="margin-top: 15px; padding: 10px; background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; color: #856404;">
                    <strong>⚠️ Atenção:</strong> Esta ação criará um backup automático antes da remoção, mas é irreversível.
                </div>
            `;
            
            infoContent.innerHTML = html;
            btnRemover.disabled = false;
        })
        .catch(error => {
            console.error('Erro:', error);
            infoContent.innerHTML = '<div style="color: #dc3545;">❌ Erro ao carregar informações da disciplina</div>';
        });
}

function removerDisciplinaPrincipal() {
    const disciplina = document.getElementById('disciplina-principal-remover').value;
    const periodo = document.getElementById('periodo-principal-remover').value;
    
    if (!disciplina) {
        mostrarAlerta('Selecione uma disciplina para remover.', 'error');
        return;
    }
    
    const mensagem = periodo 
        ? `Tem certeza que deseja remover a disciplina "${disciplina}" - Período ${periodo}?\n\nEsta ação criará um backup automático, mas é irreversível.`
        : `Tem certeza que deseja remover a disciplina "${disciplina}" completa?\n\nEsta ação criará um backup automático, mas é irreversível.`;
    
    if (!confirm(mensagem)) {
        return;
    }
    
    // Mostra loading
    const btnRemover = document.getElementById('btn-remover-disciplina-principal');
    const textoOriginal = btnRemover.innerHTML;
    btnRemover.innerHTML = '⏳ Removendo...';
    btnRemover.disabled = true;
    
    const dados = { disciplina: disciplina };
    if (periodo) {
        dados.periodo = periodo;
    }
    
    fetch('/admin/remover-disciplina-principal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(dados)
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            document.getElementById('disciplina-principal-remover').value = '';
            document.getElementById('periodo-principal-remover').value = '';
            document.getElementById('btn-remover-disciplina-principal').disabled = true;
            document.getElementById('info-disciplina-principal').style.display = 'none';
            
            // Recarrega disciplinas disponíveis
            carregarDisciplinasPrincipais();
            
            // Mostra detalhes da remoção
            setTimeout(() => {
                mostrarAlerta(`✅ Backup criado: ${data.backup_criado}\n📊 ${data.total_perguntas_removidas} perguntas removidas`, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao remover disciplina.', 'error');
    })
    .finally(() => {
        btnRemover.innerHTML = textoOriginal;
        btnRemover.disabled = false;
    });
}

function carregarBackupsPrincipal() {
    const listaBackups = document.getElementById('lista-backups-principal');
    
    // Mostra loading
    listaBackups.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <div style="color: #007bff; font-size: 24px; margin-bottom: 10px;">⏳</div>
            <p>Carregando backups...</p>
        </div>
    `;
    
    fetch('/admin/listar-backups-principal')
        .then(response => response.json())
        .then(data => {
            if (data.erro) {
                listaBackups.innerHTML = `<div style="color: #dc3545; text-align: center; padding: 40px;">❌ Erro: ${data.erro}</div>`;
                return;
            }
            
            if (data.backups.length === 0) {
                listaBackups.innerHTML = `
                    <div style="text-align: center; color: #6c757d; padding: 40px;">
                        <div style="font-size: 48px; color: #ccc; margin-bottom: 20px;">💾</div>
                        <h4>Nenhum backup encontrado</h4>
                        <p>Os backups aparecerão aqui quando você remover disciplinas/períodos.</p>
                    </div>
                `;
                atualizarEstatisticasBackupsPrincipal(data.backups);
                return;
            }
            
            // Renderiza lista de backups
            listaBackups.innerHTML = data.backups.map(backup => `
                <div class="disciplina-item">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                        <div>
                            <h4>📚 ${backup.disciplina}${backup.periodo ? ' - Período ' + backup.periodo : ''}</h4>
                            <p style="color: #666; margin: 5px 0;">📅 Criado em: ${backup.data_criacao}</p>
                            <p style="color: #666; margin: 5px 0;">📁 Arquivo: ${backup.filename}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.2em; font-weight: bold; color: #007bff;">${backup.total_perguntas}</div>
                            <div style="color: #666; font-size: 0.9em;">perguntas</div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; justify-content: flex-end;">
                        <button class="btn primary" onclick="restaurarBackupPrincipal('${backup.filename}')">
                            🔄 Restaurar
                        </button>
                        <button class="btn danger" onclick="excluirBackupPrincipal('${backup.filename}')">
                            🗑️ Excluir Backup
                        </button>
                    </div>
                </div>
            `).join('');
            
            atualizarEstatisticasBackupsPrincipal(data.backups);
        })
        .catch(error => {
            console.error('Erro:', error);
            listaBackups.innerHTML = '<div style="color: #dc3545; text-align: center; padding: 40px;">❌ Erro ao carregar backups</div>';
        });
}

function restaurarBackupPrincipal(filename) {
    if (!confirm(`Tem certeza que deseja restaurar este backup?\n\nArquivo: ${filename}\n\nSe a disciplina/período já existir, ele será substituído.`)) {
        return;
    }
    
    fetch('/admin/restaurar-backup-principal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            carregarDisciplinasPrincipais();
            carregarBackupsPrincipal();
            
            // Mostra detalhes da restauração
            setTimeout(() => {
                const msg = data.disciplina_existente_substituida 
                    ? `⚠️ Disciplina/período existente foi substituído.\n📊 ${data.total_perguntas_restauradas} perguntas restauradas`
                    : `📊 ${data.total_perguntas_restauradas} perguntas restauradas`;
                mostrarAlerta(msg, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao restaurar backup.', 'error');
    });
}

function excluirBackupPrincipal(filename) {
    if (!confirm(`Tem certeza que deseja excluir este backup?\n\nArquivo: ${filename}\n\nEsta ação é irreversível.`)) {
        return;
    }
    
    fetch('/admin/excluir-backup-principal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename })
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            carregarBackupsPrincipal(); // Recarrega a lista
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao excluir backup.', 'error');
    });
}

function restaurarTodosBackupsPrincipal() {
    if (!confirm(`Tem certeza que deseja restaurar TODOS os backups do quiz principal?\n\n⚠️ ATENÇÃO:\n- Esta ação criará um backup do estado atual\n- Todas as disciplinas/períodos em backup serão restaurados\n- Disciplinas/períodos existentes serão substituídos\n- Esta ação pode demorar alguns segundos\n\nDeseja continuar?`)) {
        return;
    }
    
    // Mostra loading
    const btnRestaurar = document.getElementById('btn-restaurar-todos-principal');
    const textoOriginal = btnRestaurar.innerHTML;
    btnRestaurar.innerHTML = '⏳ Restaurando...';
    btnRestaurar.disabled = true;
    
    fetch('/admin/restaurar-todos-backups-principal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            carregarDisciplinasPrincipais();
            carregarBackupsPrincipal();
            
            // Mostra detalhes da restauração
            setTimeout(() => {
                let msg = `✅ Restauração completa realizada!\n\n`;
                msg += `📊 ${data.total_backups_restaurados} backups restaurados\n`;
                msg += `❓ ${data.total_perguntas_restauradas} perguntas restauradas\n\n`;
                
                if (data.disciplinas_restauradas.length > 0) {
                    msg += `📚 Disciplinas restauradas: ${data.disciplinas_restauradas.join(', ')}\n`;
                }
                
                if (data.disciplinas_substituidas.length > 0) {
                    msg += `⚠️ Disciplinas substituídas: ${data.disciplinas_substituidas.join(', ')}\n`;
                }
                
                msg += `\n💾 Backup do estado atual: ${data.backup_estado_atual}`;
                
                mostrarAlerta(msg, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao restaurar todos os backups.', 'error');
    })
    .finally(() => {
        btnRestaurar.innerHTML = textoOriginal;
        btnRestaurar.disabled = false;
    });
}

function limparTodosBackupsPrincipal() {
    if (!confirm(`Tem certeza que deseja excluir TODOS os backups do quiz principal?\n\n⚠️ ATENÇÃO:\n- Esta ação criará um backup do estado atual\n- TODOS os arquivos de backup serão removidos permanentemente\n- Esta ação é irreversível\n- Você não poderá restaurar as disciplinas/períodos removidos\n\nDeseja continuar?`)) {
        return;
    }
    
    // Mostra loading
    const btnLimpar = document.getElementById('btn-limpar-todos-principal');
    const textoOriginal = btnLimpar.innerHTML;
    btnLimpar.innerHTML = '⏳ Limpando...';
    btnLimpar.disabled = true;
    
    fetch('/admin/limpar-todos-backups-principal', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.sucesso) {
            mostrarAlerta(data.mensagem, 'success');
            
            // Atualiza informações
            carregarBackupsPrincipal();
            
            // Mostra detalhes da limpeza
            setTimeout(() => {
                let msg = `✅ Limpeza de backups realizada!\n\n`;
                msg += `🗑️ ${data.total_backups_removidos} backups removidos\n`;
                msg += `💾 Backup do estado atual: ${data.backup_estado_atual}\n\n`;
                msg += `📁 Arquivos removidos:\n`;
                data.arquivos_removidos.forEach(arquivo => {
                    msg += `  - ${arquivo}\n`;
                });
                
                mostrarAlerta(msg, 'info');
            }, 1000);
            
        } else {
            mostrarAlerta('Erro: ' + (data.erro || 'Erro desconhecido'), 'error');
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        mostrarAlerta('Erro ao limpar todos os backups.', 'error');
    })
    .finally(() => {
        btnLimpar.innerHTML = textoOriginal;
        btnLimpar.disabled = false;
    });
}

function atualizarEstatisticasBackupsPrincipal(backups) {
    document.getElementById('total-backups-principal').textContent = backups.length;
    
    // Conta disciplinas únicas
    const disciplinasUnicas = new Set(backups.map(b => b.disciplina));
    document.getElementById('disciplinas-backup-principal').textContent = disciplinasUnicas.size;
    
    // Soma total de perguntas
    const totalPerguntas = backups.reduce((sum, backup) => sum + backup.total_perguntas, 0);
    document.getElementById('total-perguntas-backup-principal').textContent = totalPerguntas;
    
    // Habilita/desabilita botões de ação em massa
    const btnRestaurarTodos = document.getElementById('btn-restaurar-todos-principal');
    const btnLimparTodos = document.getElementById('btn-limpar-todos-principal');
    
    if (backups.length > 0) {
        btnRestaurarTodos.disabled = false;
        btnLimparTodos.disabled = false;
    } else {
        btnRestaurarTodos.disabled = true;
        btnLimparTodos.disabled = true;
    }
}

// ========================================
// INICIALIZAÇÃO
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Adiciona listeners para atualização automática
    document.querySelectorAll('#opcoes-lista input').forEach(input => {
        input.addEventListener('input', atualizarSelectResposta);
    });
    
    // Inicializa botão de adicionar opção
    atualizarBotaoAdicionar();
    
    // Adiciona listener para drag and drop
    const uploadArea = document.getElementById('upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.style.borderColor = '#007bff';
            uploadArea.style.background = '#f8f9fa';
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadArea.style.borderColor = '#ddd';
            uploadArea.style.background = 'transparent';
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.style.borderColor = '#ddd';
            uploadArea.style.background = 'transparent';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                document.getElementById('arquivo-upload').files = files;
                arquivoSelecionado();
            }
        });
    }
}); 