// Variáveis globais para armazenar o ID da revisão atual e sugestão de qualidade
let revisaoAtual = null;
let suggestedQuality = null; // 0,3,4,5
const startTimes = {}; // mapa revisaoId -> timestamp (ms)
const flashcardViewed = {}; // revisaoId -> true se mostrou resposta ou clicou sugestão
const quizAnswered = {};    // revisaoId -> true se escolheu alternativa

// Função para cadastrar novo estudo via AJAX
function cadastrarEstudo(event) {
    event.preventDefault();
    
    const materia = document.getElementById('materia').value.trim();
    const topico = document.getElementById('topico').value.trim();
    
    if (!materia || !topico) {
        alert('Por favor, preencha todos os campos obrigatórios!');
        return;
    }
    
    
    fetch('/cadastrar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            materia: materia,
            topico: topico
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'sucesso') {
            alert('Estudo cadastrado com sucesso!');
            document.getElementById('materia').value = '';
            document.getElementById('topico').value = '';
            window.location.reload();
        } else {
            alert('Erro: ' + data.mensagem);
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao cadastrar estudo. Tente novamente.');
    });
}

// NOVA FUNÇÃO: Verificar resposta do Quiz e sugerir qualidade
function verificarQuiz(revisaoId, respostaCorreta, alternativaEscolhida, grupoId) {
    // Iniciar tempo ao primeiro clique se ainda não iniciado
    if (!startTimes[revisaoId]) startTimes[revisaoId] = Date.now();
    // Marcar visualmente
    const container = document.getElementById(grupoId);
    if (container) {
        const btns = container.querySelectorAll('button[data-alt]');
        btns.forEach(b => b.disabled = true);
        btns.forEach(b => {
            const alt = b.getAttribute('data-alt');
            if (alt === respostaCorreta) {
                b.classList.remove('btn-outline-secondary');
                b.classList.add('btn-success');
            }
        });
        const chosen = container.querySelector(`button[data-alt="${alternativaEscolhida}"]`);
        if (chosen && alternativaEscolhida !== respostaCorreta) {
            chosen.classList.remove('btn-outline-secondary');
            chosen.classList.add('btn-danger');
        }
    }

    // Sugerir qualidade
    const quality = alternativaEscolhida === respostaCorreta ? 4 : 0;
    sugerirQualidade(revisaoId, quality);
    quizAnswered[revisaoId] = true;

    // Feedback textual abaixo das alternativas
    const fb = document.getElementById(`${grupoId}-fb`);
    if (fb) {
        if (alternativaEscolhida === respostaCorreta) {
            fb.innerHTML = '<div class="alert alert-success py-2 mb-0">Correto!</div>';
        } else {
            fb.innerHTML = '<div class="alert alert-danger py-2 mb-0">Resposta incorreta</div>';
        }
    }
}

// Iniciar tempo explicitamente (ex.: ao clicar Mostrar resposta do Flashcard)
function iniciarTempo(revisaoId) {
    if (!startTimes[revisaoId]) startTimes[revisaoId] = Date.now();
}

// Registrar que o flashcard foi estudado (chamar ao mostrar resposta ou ao clicar Errei/Acertei)
function registrarFlashcardVista(revisaoId) {
    flashcardViewed[revisaoId] = true;
    iniciarTempo(revisaoId);
}

// NOVA FUNÇÃO: Sugere qualidade (Acertou/Errou) e abre o modal
function sugerirQualidade(revisaoId, quality) {
    revisaoAtual = revisaoId;
    suggestedQuality = quality; // ex.: 4 (Acertou) ou 0 (Errou)
    const modalElement = document.getElementById('modalAvaliacao');
    const modal = new bootstrap.Modal(modalElement);
    atualizarSugestaoNoModal();
    modal.show();
}

// Atualiza a área de sugestão no modal
function atualizarSugestaoNoModal() {
    const box = document.getElementById('suggestionBox');
    const text = document.getElementById('suggestionText');
    if (!box || !text) return;
    if (suggestedQuality === null) {
        box.style.display = 'none';
        text.textContent = '';
        return;
    }
    const label = suggestedQuality === 0 ? 'Errou (0)' :
                  suggestedQuality === 3 ? 'Lembrou com dificuldade (3)' :
                  suggestedQuality === 4 ? 'Acertou (4)' :
                  suggestedQuality === 5 ? 'Perfeito (5)' : `${suggestedQuality}`;
    text.textContent = `Sugestão de qualidade: ${label}. Você pode ajustar abaixo se quiser.`;
    box.style.display = 'block';
}

// NOVA FUNÇÃO: Abre o modal e armazena o ID da revisão
function marcarFeita(revisaoId, modo) {
    // Armazena o ID da revisão na variável global
    revisaoAtual = revisaoId;
    // Ao abrir manualmente, limpa sugestão
    suggestedQuality = null;
    // Guardas de interação
    if (modo === 'flashcard') {
        if (!flashcardViewed[revisaoId]) {
            alert('Veja a resposta ou use Errei/Acertei antes de concluir.');
            return;
        }
    }
    if (modo === 'quiz') {
        if (!quizAnswered[revisaoId]) {
            alert('Responda ao quiz antes de concluir.');
            return;
        }
    }
    // Se ainda não iniciamos o cronômetro, iniciar agora
    if (!startTimes[revisaoId]) startTimes[revisaoId] = Date.now();
    
    // Abre o modal usando Bootstrap
    const modalElement = document.getElementById('modalAvaliacao');
    const modal = new bootstrap.Modal(modalElement);
    atualizarSugestaoNoModal();
    modal.show();
}

// NOVA FUNÇÃO: Envia a qualidade para o backend
function enviarQualidade(quality) {
    if (revisaoAtual === null) {
        alert('Erro: Nenhuma revisão selecionada');
        return;
    }
    
    // Capturar nível de confiança do slider (padrão 3 se não existir)
    const slider = document.getElementById('inputConfianca');
    const nivelConfianca = slider ? parseInt(slider.value) : 3;

    // Calcular tempo de resposta (segundos)
    let tempoResposta = null;
    if (startTimes[revisaoAtual]) {
        tempoResposta = Math.max(0, Math.round((Date.now() - startTimes[revisaoAtual]) / 1000));
    }

    // Interação detectada?
    const interagiu = !!flashcardViewed[revisaoAtual] || !!quizAnswered[revisaoAtual] || suggestedQuality !== null;

    // 1. Envia para o backend
    fetch(`/marcar/${revisaoAtual}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ quality: quality, nivel_confianca: nivelConfianca, tempo_resposta: tempoResposta, interagiu: interagiu })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            // 2. Fecha o modal
            const modalElement = document.getElementById('modalAvaliacao');
            const modal = bootstrap.Modal.getInstance(modalElement);
            modal.hide();
            
            // 3. Mostra feedback com a próxima revisão
            alert(`✅ Revisão concluída!\n\nPróxima revisão: ${data.proxima_revisao}\nIntervalo: ${data.intervalo_dias} dias`);
            
            // 4. Remove o card da tela com animação (usando data-revisao-id)
            const card = document.querySelector(`.card[data-revisao-id="${revisaoAtual}"]`);
            if (card) {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'translateX(-100%)';
            
                setTimeout(() => {
                    card.remove();
                    
                    // Recarrega se não houver mais revisões
                    const cards = document.querySelectorAll('.card');
                    if (cards.length === 0) {
                        location.reload();
                    }
                }, 300);
            }
            
            // 5. Limpeza de estado desta revisão
            const doneId = revisaoAtual;
            delete startTimes[doneId];
            delete flashcardViewed[doneId];
            delete quizAnswered[doneId];
            revisaoAtual = null;
        } else {
            alert('Erro: ' + data.mensagem);
        }
    })
    .catch(error => {
        console.error('Erro:', error);
        alert('Erro ao marcar como feita. Tente novamente.');
    });
}

// Adicionar event listeners quando o DOM carregar
document.addEventListener('DOMContentLoaded', function() {
    // Listener para formulário de cadastro
    const form = document.querySelector('form[action="/cadastrar"]');
    if (form) {
        form.addEventListener('submit', cadastrarEstudo);
    }
    
    // NOVO: Listeners para os botões de qualidade
    const qualityButtons = document.querySelectorAll('.quality-btn');
    qualityButtons.forEach(button => {
        button.addEventListener('click', function() {
            const quality = parseInt(this.getAttribute('data-quality'));
            enviarQualidade(quality);
        });
    });
    
    // NOVO: Atualizar rótulo do nível de confiança ao mover o slider
    const slider = document.getElementById('inputConfianca');
    const label = document.getElementById('labelConfianca');
    if (slider && label) {
        const updateLabel = () => { label.textContent = slider.value; };
        slider.addEventListener('input', updateLabel);
        slider.addEventListener('change', updateLabel);
        updateLabel();
    }
    
    // Validação em tempo real
    const materiaInput = document.getElementById('materia');
    const topicoInput = document.getElementById('topico');
    
    if (materiaInput && topicoInput) {
        [materiaInput, topicoInput].forEach(input => {
            input.addEventListener('blur', function() {
                if (!this.value.trim()) {
                    this.classList.add('is-invalid');
                } else {
                    this.classList.remove('is-invalid');
                }
            });
        });
    }

    // Delegação: Mostrar resposta do flashcard
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-show-answer');
        if (!btn) return;
        const id = Number(btn.dataset.revisaoId);
        registrarFlashcardVista(id);
    });

    // Delegação: Sugestões de qualidade (Errei/Acertei) para flashcards
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-flash-suggest');
        if (!btn) return;
        const id = Number(btn.dataset.revisaoId);
        const quality = parseInt(btn.dataset.quality);
        registrarFlashcardVista(id);
        sugerirQualidade(id, quality);
    });

    // Delegação: Responder Quiz
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-quiz');
        if (!btn) return;
        const id = Number(btn.dataset.revisaoId);
        const correta = btn.dataset.correta ? JSON.parse(btn.dataset.correta) : null;
        const alt = btn.dataset.alt;
        const groupId = btn.dataset.groupId;
        verificarQuiz(id, correta, alt, groupId);
    });

    // Delegação: Marcar Feita
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.btn-marcar');
        if (!btn) return;
        const id = Number(btn.dataset.revisaoId);
        const modo = btn.dataset.modo;
        marcarFeita(id, modo);
    });
});