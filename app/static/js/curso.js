            // --- VARIÁVEIS GLOBAIS ---
            let currentPage = 1;
            const totalPages = 5; // <--- ATUALIZADO para refletir 20 módulos (5 páginas x 4 módulos)
            let currentLessonId = null;

            // Armazenamento local (Simulação de progresso do usuário)
            const storageKey = 'pythonCourseProgress';
            let progressData = JSON.parse(localStorage.getItem(storageKey)) || {};

            // --- FUNÇÕES DE LÓGICA DO CURSO (Mantidas/Adaptadas) ---

            /**
             * Salva o estado do progresso no Local Storage.
             */
            function saveProgress() {
                localStorage.setItem(storageKey, JSON.stringify(progressData));
                updateUI();
                updateGlobalProgress();
            }

            /**
             * Marca uma lição como concluída/assistida.
             * @param {string} lessonId - ID da lição (ex: '1-A1', '2-1').
             */
            function markAsCompleted(lessonId) {
                progressData[lessonId] = true;
                saveProgress();
                
                // Se for atividade, ajusta o botão do modal
                const checkButton = document.getElementById('check-activity-btn');
                const completeButton = document.getElementById('complete-activity-btn');
                if (checkButton && completeButton) {
                    // Apenas altera se o botão está visível no modal
                    if (checkButton.style.display !== 'none') {
                        checkButton.textContent = "✅ ATIVIDADE CORRIGIDA E CONCLUÍDA";
                        checkButton.disabled = true;
                        checkButton.style.background = '#00ff88';
                        checkButton.style.color = '#111';
                    }
                    
                    if (completeButton.style.display !== 'none') {
                        completeButton.textContent = "✅ CONCLUÍDO";
                        completeButton.classList.add('completed');
                        completeButton.disabled = true;
                    }
                }
            }

            /**
             * Desmarca uma lição como concluída/assistida.
             * @param {string} lessonId - ID da lição.
             */
            function unmarkAsCompleted(lessonId) {
                delete progressData[lessonId];
                saveProgress();
            }

            /**
             * Atualiza os ícones na UI (círculo vazio vs. checkmark) e botões de desmarcar.
             */
            function updateUI() {
                document.querySelectorAll('[data-lesson-id]').forEach(element => {
                    const lessonId = element.dataset.lessonId;
                    const lessonWrapper = element.closest('.lesson-item-wrapper');
                    if (!lessonWrapper) return; // Garante que estamos dentro de um wrapper

                    const link = lessonWrapper.querySelector('a');
                    const icon = link.querySelector('.lesson-icon i');
                    const unwatchBtn = lessonWrapper.querySelector('.unwatch-btn');
                    
                    if (progressData[lessonId]) {
                        link.classList.add('watched');
                        icon.className = 'fas fa-check-circle';
                        if (unwatchBtn) unwatchBtn.style.display = 'inline-block';
                    } else {
                        link.classList.remove('watched');
                        icon.className = 'far fa-circle';
                        if (unwatchBtn) unwatchBtn.style.display = 'none';
                    }
                });

                // Atualizar progresso do módulo e cor do card
                document.querySelectorAll('.course-card').forEach(card => {
                    const moduleId = card.dataset.moduleId;
                    updateModuleProgress(moduleId);
                });
            }

            /**
             * Calcula e atualiza o progresso de um módulo específico.
             */
            function updateModuleProgress(moduleId) {
                const card = document.querySelector(`.course-card[data-module-id="${moduleId}"]`);
                if (!card) return;

                const allItems = card.querySelectorAll('[data-lesson-id]');
                const totalItems = allItems.length;
                let completedItems = 0;

                allItems.forEach(item => {
                    const lessonId = item.dataset.lessonId;
                    if (progressData[lessonId]) {
                        completedItems++;
                    }
                });

                const percentage = totalItems === 0 ? 0 : Math.round((completedItems / totalItems) * 100);
                
                const progressBar = document.getElementById(`progress-bar-${moduleId}`);
                const progressLabel = document.getElementById(`progress-label-${moduleId}`);

                if (progressBar && progressLabel) {
                    progressBar.style.width = `${percentage}%`;
                    progressLabel.textContent = `${percentage}% concluído`;

                    if (percentage === 100) {
                        progressBar.classList.add('completed');
                        progressLabel.classList.add('completed');
                    } else {
                        progressBar.classList.remove('completed');
                        progressLabel.classList.remove('completed');
                    }
                }
            }
            
            /**
             * Atualiza o dashboard de progresso global.
             */
            function updateGlobalProgress() {
                const allItems = document.querySelectorAll('.course-card [data-lesson-id]');
                const totalItems = allItems.length;
                const completedItems = Object.keys(progressData).length;
                const globalPercentage = totalItems === 0 ? 0 : Math.round((completedItems / totalItems) * 100);

                // Contagem de Módulos (Simulação: um módulo é completo se o progresso for 100%)
                const totalModules = document.querySelectorAll('.course-card').length;
                let completedModules = 0;
                for (let i = 1; i <= totalModules; i++) {
                    const progressBar = document.getElementById(`progress-bar-${i}`);
                    if (progressBar && progressBar.style.width === '100%') {
                        completedModules++;
                    }
                }
                
                document.getElementById('global-watched-count').textContent = `${completedItems} / ${totalItems}`;
                document.getElementById('global-modules-count').textContent = `${completedModules}/${totalModules}`;
                document.getElementById('global-progress-percent').textContent = `${globalPercentage}%`;
            }

            // --- FUNÇÕES DE PAGINAÇÃO (Mantidas) ---

            function showPage(pageNumber) {
                document.querySelectorAll('.course-grid.page').forEach(page => {
                    page.classList.remove('active-page');
                });

                const activePage = document.querySelector(`.course-grid.page[data-page="${pageNumber}"]`);
                if (activePage) {
                    activePage.classList.add('active-page');
                }

                currentPage = pageNumber;
                updatePaginationControls();
            }

            function updatePaginationControls() {
                document.getElementById('page-indicator').textContent = `Página ${currentPage} de ${totalPages}`;
                document.getElementById('prev-page-btn').disabled = (currentPage === 1);
                document.getElementById('next-page-btn').disabled = (currentPage === totalPages);
            }
            
            // --- FUNÇÕES DO MODAL (Adaptadas para Correção) ---

            /**
             * Abre o modal de Atividade.
             */
            document.querySelectorAll('.open-modal-activity').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    currentLessonId = this.dataset.lessonId;
                    const title = this.dataset.activityTitle;
                    const desc = this.dataset.activityDesc;
                    
                    const modal = document.getElementById('activity-modal');
                    const titleEl = document.getElementById('activity-modal-title');
                    const descEl = document.getElementById('activity-modal-description');
                    const codeInput = document.getElementById('activity-code-input');
                    const completeButton = document.getElementById('complete-activity-btn');
                    const checkButton = document.getElementById('check-activity-btn');
                    const feedbackOutput = document.getElementById('activity-feedback-output');
                    const inputTitle = document.getElementById('input-title');

                    // 1. Limpa o feedback e campos
                    feedbackOutput.textContent = 'O feedback do seu código aparecerá aqui.';
                    feedbackOutput.classList.remove('feedback-success', 'feedback-failure');
                    
                    // 2. Preenche os dados
                    titleEl.textContent = title;
                    descEl.textContent = desc;
                    
                    // 3. Checa se o item está concluído
                    const isCompleted = progressData[currentLessonId];
                    
                    // 4. Configura o Input e Botões
                    const isCodeActivity = ['1-A1', '1-A2'].includes(currentLessonId);

                    if (isCodeActivity) {
                        codeInput.style.display = 'block';
                        checkButton.style.display = 'block';
                        completeButton.style.display = 'none'; 
                        inputTitle.textContent = 'Seu Código Python (Insira a função completa):';

                        if (isCompleted) {
                            checkButton.textContent = "✅ ATIVIDADE CORRIGIDA E CONCLUÍDA";
                            checkButton.disabled = true;
                            checkButton.style.background = '#00ff88';
                            checkButton.style.color = '#111';
                        } else {
                            checkButton.textContent = "<i class=\"fas fa-check-circle\"></i> CORRIGIR ATIVIDADE";
                            checkButton.disabled = false;
                            checkButton.style.background = '#3498db';
                            checkButton.style.color = '#fff';
                        }

                    } else {
                        // Atividades teóricas ou avançadas que não são testadas pelo JS
                        codeInput.style.display = 'none'; 
                        checkButton.style.display = 'none';
                        completeButton.style.display = 'block';
                        inputTitle.textContent = 'Observações:';
                        
                        if (isCompleted) {
                            completeButton.textContent = "✅ CONCLUÍDO";
                            completeButton.classList.add('completed');
                            completeButton.disabled = true;
                        } else {
                            completeButton.textContent = "Marcar como Concluído";
                            completeButton.classList.remove('completed');
                            completeButton.disabled = false;
                        }

                    }

                    modal.classList.add('open');
                });
            });
            
            /**
             * Abre o modal de Vídeo. (Mantida)
             */
            document.querySelectorAll('.open-video-modal').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    currentLessonId = this.dataset.lessonId;
                    const title = this.dataset.videoTitle;
                    let url = this.dataset.videoUrl;
                    
                    // Convert YouTube URL to embed format (if necessary)
                    if (url.includes('youtu.be') || url.includes('youtube.com/watch')) {
                        const videoId = url.split('/').pop().split('=').pop().split('&')[0];
                        url = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
                    }

                    document.getElementById('video-modal-title').textContent = title;
                    document.getElementById('video-iframe').src = url;

                    const completeButton = document.getElementById('complete-video-btn');
                    if (progressData[currentLessonId]) {
                        completeButton.textContent = "✅ CONCLUÍDO";
                        completeButton.classList.add('completed');
                        completeButton.disabled = true;
                    } else {
                        completeButton.textContent = "Marcar Aula como Concluída";
                        completeButton.classList.remove('completed');
                        completeButton.disabled = false;
                    }

                    document.getElementById('video-modal').classList.add('open');
                });
            });
            
            /**
             * Fecha qualquer modal. (Adaptada)
             */
            document.querySelectorAll('.modal-close-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    const modalId = this.dataset.modal;
                    const modal = document.getElementById(modalId);
                    modal.classList.remove('open');
                    
                    // Parar vídeo se for o modal de vídeo
                    if (modalId === 'video-modal') {
                        document.getElementById('video-iframe').src = '';
                    }
                    
                    // Limpar campos de input da atividade
                    if (modalId === 'activity-modal') {
                        document.getElementById('activity-code-input').value = '';
                        document.getElementById('activity-feedback-output').textContent = 'O feedback do seu código aparecerá aqui.';
                        document.getElementById('activity-feedback-output').classList.remove('feedback-success', 'feedback-failure');
                    }
                    currentLessonId = null;
                });
            });
            
            // --- EVENT LISTENERS GERAIS (Mantidos) ---

            // Pular página
            document.getElementById('prev-page-btn').addEventListener('click', () => {
                if (currentPage > 1) {
                    showPage(currentPage - 1);
                }
            });

            document.getElementById('next-page-btn').addEventListener('click', () => {
                if (currentPage < totalPages) {
                    showPage(currentPage + 1);
                }
            });

            document.querySelectorAll('.unwatch-btn').forEach(btn => {
                btn.addEventListener('click', function(e) {
                    e.stopPropagation(); 
                    const lessonId = this.dataset.lessonId;
                    unmarkAsCompleted(lessonId);
                });
            });

            document.getElementById('complete-video-btn').addEventListener('click', function() {
                if (currentLessonId && !this.classList.contains('completed')) {
                    markAsCompleted(currentLessonId);
                    document.querySelector('.modal-close-btn[data-modal="video-modal"]').click();
                }
            });

            document.getElementById('complete-activity-btn').addEventListener('click', function() {
                // Este botão só é exibido para atividades não-código (3-A1, 4-A1, etc.)
                if (currentLessonId && !this.classList.contains('completed')) {
                    markAsCompleted(currentLessonId);
                    document.querySelector('.modal-close-btn[data-modal="activity-modal"]').click();
                }
            });

            const activityTests = {
                '1-A1': {
                    funcName: 'calcular_imc',
                    testCases: [
                        { inputs: [70, 1.75], expected: 22.86, precision: 2 }, 
                        { inputs: [90, 1.80], expected: 27.78, precision: 2 },
                        { inputs: [55, 1.60], expected: 21.48, precision: 2 }
                    ]
                },
                '1-A2': {
                    funcName: 'inverter_string',
                    testCases: [
                        { inputs: ['Python'], expected: 'nohtyP' },
                        { inputs: ['hello'], expected: 'olleh' },
                        { inputs: ['',], expected: '' },
                        { inputs: ['12345'], expected: '54321' }
                    ]
                }
            };


            function correctActivityJS(activityId, userCode) {
                if (!userCode.trim()) {
                    return { feedback: "Por favor, insira seu código Python para correção. Certifique-se de incluir a definição completa da função.", passed: false };
                }

                const testConfig = activityTests[activityId];
                if (!testConfig) {
                    return { feedback: `ID de Atividade '${activityId}' não suportado ou não exige correção automática.`, passed: false };
                }

                const funcName = testConfig.funcName;
                let feedback = [];
                let allPassed = true;

                try {
                    eval(userCode); 

                    if (typeof window[funcName] !== 'function') {
                        return { feedback: `❌ Erro: A função '${funcName}' não foi definida ou não está acessível globalmente.`, passed: false };
                    }

                } catch (e) {
                    return { feedback: `❌ Erro de Sintaxe/Execução no seu código: ${e.name}: ${e.message}`, passed: false };
                }

                const userFunc = window[funcName];

                testConfig.testCases.forEach((test, index) => {
                    let userResult;
                    let passed = false;
                    const inputsString = test.inputs.map(input => typeof input === 'string' ? `'${input}'` : input).join(', ');

                    try {
                        userResult = userFunc(...test.inputs);

                        if (test.precision) {
                            const userRounded = parseFloat(userResult).toFixed(test.precision);
                            const expectedRounded = test.expected.toFixed(test.precision);

                            if (userRounded === expectedRounded) {
                                passed = true;
                                feedback.push(`✅ Teste ${index + 1} (${inputsString}): Passou! Seu resultado: ${userResult} (Arredondado: ${userRounded})`);
                            } else {
                                feedback.push(`❌ Teste ${index + 1} (${inputsString}): Falhou. Esperado: ${expectedRounded}, Recebido: ${userRounded}.`);
                            }
                        } else {
                            if (userResult === test.expected) {
                                passed = true;
                                feedback.push(`✅ Teste ${index + 1} (${inputsString}): Passou! Seu resultado: '${userResult}'`);
                            } else {
                                feedback.push(`❌ Teste ${index + 1} (${inputsString}): Falhou. Esperado: '${test.expected}', Recebido: '${userResult}'.`);
                            }
                        }

                    } catch (e) {
                        feedback.push(`❌ Teste ${index + 1} (${inputsString}): Erro durante a chamada da função. Erro: ${e.message}.`);
                    }

                    if (!passed) {
                        allPassed = false;
                    }
                });

                if (allPassed) {
                    return { 
                        feedback: feedback.join('\n') + "\n\n**PARABÉNS! Seu código passou em todos os testes.**", 
                        passed: true 
                    };
                } else {
                    return { 
                        feedback: feedback.join('\n') + "\n\n**CORREÇÃO NECESSÁRIA:** Pelo menos um teste falhou. Revise a lógica da sua função.", 
                        passed: false 
                    };
                }
            }
            
            
            document.getElementById('check-activity-btn').addEventListener('click', function() {
                const userCode = document.getElementById('activity-code-input').value;
                const activityId = currentLessonId;
                const feedbackOutput = document.getElementById('activity-feedback-output');
                
                feedbackOutput.classList.remove('feedback-success', 'feedback-failure');

                const result = correctActivityJS(activityId, userCode);
                
                feedbackOutput.textContent = result.feedback;

                if (result.passed) {
                    feedbackOutput.classList.add('feedback-success');
                    markAsCompleted(activityId); 
                    
                } else {
                    feedbackOutput.classList.add('feedback-failure');
                    
                    this.textContent = "<i class=\"fas fa-exclamation-triangle\"></i> TENTE NOVAMENTE";
                }
            });

            document.addEventListener('DOMContentLoaded', () => {
                updateUI();
                updateGlobalProgress();
                showPage(currentPage);  
        
            });

// Armazenamento de progresso simulado
        let progress = JSON.parse(localStorage.getItem('courseProgress')) || {};
        let currentActId = null;
        let totalItems = 0;
        let totalModules = 20;

        // FUNÇÕES GERAIS
        function changePage(num) {
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active-page'));
            document.querySelector(`.page[data-page="${num}"]`).classList.add('active-page');
            document.querySelectorAll('.page-btn').forEach(b => b.classList.remove('active'));
            document.querySelector(`.page-btn:nth-child(${num})`).classList.add('active');
        }

        function updateProgress() {
            totalItems = 0;
            let completedItems = 0;
            let completedModules = 0;

            document.querySelectorAll('.course-card').forEach(moduleCard => {
                const moduleId = moduleCard.dataset.moduleId;
                const itemsInModule = moduleCard.querySelectorAll('.lesson-item-wrapper').length;
                let completedItemsInModule = 0;

                moduleCard.querySelectorAll('.lesson-item-wrapper').forEach(item => {
                    const lessonId = item.dataset.lessonId;
                    totalItems++;

                    if (progress[lessonId]) {
                        item.classList.add('completed');
                        item.querySelector('.lesson-icon').innerHTML = '<i class="fas fa-circle-check"></i>';
                        completedItems++;
                        completedItemsInModule++;
                    } else {
                        item.classList.remove('completed');
                        item.querySelector('.lesson-icon').innerHTML = '<i class="far fa-circle"></i>';
                    }
                });

                const moduleProgressPercent = itemsInModule > 0 ? (completedItemsInModule / itemsInModule) * 100 : 0;
                
                const progressBar = document.getElementById(`progress-bar-${moduleId}`);
                const progressLabel = document.getElementById(`progress-label-${moduleId}`);

                if (progressBar) progressBar.style.width = `${moduleProgressPercent.toFixed(0)}%`;
                if (progressLabel) progressLabel.innerText = `${moduleProgressPercent.toFixed(0)}% concluído`;

                if (moduleProgressPercent === 100) {
                    completedModules++;
                }
            });

            const globalProgressPercent = totalItems > 0 ? (completedItems / totalItems) * 100 : 0;

            document.getElementById('global-watched-count').innerText = `${completedItems}/${totalItems}`;
            document.getElementById('global-modules-count').innerText = `${completedModules}/${totalModules}`;
            document.getElementById('global-progress-percent').innerText = `${globalProgressPercent.toFixed(1)}%`;

            localStorage.setItem('courseProgress', JSON.stringify(progress));
        }

        // EVENTOS DE MARCAÇÃO
        document.querySelectorAll('.open-video-modal').forEach(link => {
            link.onclick = function(e) {
                e.preventDefault();
                currentActId = this.parentElement.dataset.lessonId;
                document.getElementById('modal-video-title').innerText = this.dataset.videoTitle;
                document.getElementById('video-modal').style.display = 'block';

                // Marcar como concluído ao fechar o modal ou usar o botão
                document.getElementById('mark-watched-btn').onclick = () => {
                    progress[currentActId] = true;
                    updateProgress();
                    document.getElementById('video-modal').style.display = 'none';
                };
            };
        });

        document.querySelectorAll('.unwatch-btn').forEach(btn => {
            btn.onclick = function(e) {
                e.stopPropagation(); // Evita que o clique abra o modal
                const lessonId = this.dataset.lessonId;
                delete progress[lessonId];
                updateProgress();
            };
        });

        // ABRIR MODAL DE ATIVIDADE
        document.querySelectorAll('.open-modal-activity').forEach(link => {
            link.onclick = function(e) {
                e.preventDefault();
                currentActId = this.parentElement.dataset.lessonId;
                document.getElementById('modal-activity-title').innerText = this.dataset.activityTitle;
                document.getElementById('modal-activity-desc').innerText = this.dataset.activityDesc;
                document.getElementById('correction-result').style.display = 'none';
                document.getElementById('correction-result').className = "result-message";
                document.getElementById('student-code').value = '';
                document.getElementById('submit-activity-btn').disabled = false;
                document.getElementById('submit-activity-btn').innerText = "Corrigir Atividade";
                document.getElementById('activity-modal').style.display = 'block';
            };
        });

        // FECHAR MODAIS
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.onclick = () => {
                document.getElementById('activity-modal').style.display = 'none';
                document.getElementById('video-modal').style.display = 'none';
            };
        });

        // FUNÇÃO DE CORREÇÃO (O core do desafio)
        function runCorrection() {
            const code = document.getElementById('student-code').value;
            const resultBox = document.getElementById('correction-result');
            const btn = document.getElementById('submit-activity-btn');
            
            if (code.trim().length < 10) {
                resultBox.className = "result-message result-error";
                resultBox.innerHTML = "❌ <b>Código muito curto!</b> Insira pelo menos 10 caracteres.";
                resultBox.style.display = 'block';
                return;
            }

            btn.disabled = true;
            btn.innerText = "Processando no Servidor...";
            resultBox.style.display = 'none';

            // Simulação de verificação backend
            setTimeout(() => {
                let success = false;
                const normalizedCode = code.toLowerCase();

                // Lógica de validação baseada no lessonId (para simular correção específica)
                if (currentActId === '1-A1' && normalizedCode.includes('def calcular_imc(')) success = true;
                else if (currentActId === '2-A1' && normalizedCode.includes('class contabancaria')) success = true;
                else if (currentActId === '3-A1' && normalizedCode.includes('@app.post') && normalizedCode.includes('@app.get')) success = true;
                else if (currentActId === '4-A1' && normalizedCode.includes('select') && normalizedCode.includes('update')) success = true;
                else if (currentActId === '9-A1' && normalizedCode.includes('from python:') && normalizedCode.includes('copy')) success = true;
                else if (currentActId === '10-A1' && normalizedCode.includes('beautifulsoup')) success = true;
                else if (currentActId === '20-A1' && normalizedCode.includes('https://github.com/')) success = true;
                else if (normalizedCode.includes('def') || normalizedCode.includes('import') || normalizedCode.includes('class')) success = true;
                else success = Math.random() < 0.8; // Chance de sucesso para desafios não específicos

                btn.disabled = false;
                btn.innerText = "Corrigir Atividade";
                resultBox.style.display = 'block';

                if (success) {
                    resultBox.className = "result-message result-success";
                    resultBox.innerHTML = "✅ <b>Código Aprovado!</b> Parabéns, sua solução foi validada. (Progresso Registrado)";
                    progress[currentActId] = true;
                    updateProgress();
                } else {
                    resultBox.className = "result-message result-error";
                    resultBox.innerHTML = "❌ <b>Ops!</b> Seu código não atende aos requisitos ou contém erros de lógica simulados.";
                }
            }, 1500);
        }

        // Inicialização
        document.addEventListener('DOMContentLoaded', updateProgress);
    
document.addEventListener('DOMContentLoaded', () => {

    // --- Helpers para persistência ---
    const getWatchedState = () => {
        try { return JSON.parse(localStorage.getItem('courseWatchedState') || '{}'); } catch { return {}; }
    };
    const setWatchedState = (s) => localStorage.setItem('courseWatchedState', JSON.stringify(s));

    const getActivitiesState = () => {
        try { return JSON.parse(localStorage.getItem('courseActivitiesState') || '{}'); } catch { return {}; }
    };
    const setActivitiesState = (s) => localStorage.setItem('courseActivitiesState', JSON.stringify(s));

    let watchedState = getWatchedState();
    let activitiesState = getActivitiesState();
    let currentLessonId = null;

    // --- Utilitários de UI ---
    const isActivityId = id => /-A/i.test(id);

    const updateItemUI = (lessonId) => {
        const anchor = document.querySelector(`a[data-lesson-id="${lessonId}"]`);
        if (!anchor) return;
        const icon = anchor.querySelector('.lesson-icon i');
        anchor.classList.remove('watched','wrong','pending');
        if (isActivityId(lessonId)) {
            const st = activitiesState[lessonId];
            if (st && st.status === 'correct') {
                anchor.classList.add('watched');
                if (icon) icon.className = 'fas fa-check-circle';
            } else if (st && st.status === 'wrong') {
                anchor.classList.add('wrong');
                if (icon) icon.className = 'fas fa-times-circle';
            } else if (st && st.status === 'pending') {
                anchor.classList.add('pending');
                if (icon) icon.className = 'fas fa-hourglass-half';
            } else {
                if (icon) icon.className = 'far fa-circle';
            }
        } else {
            if (watchedState[lessonId]) {
                anchor.classList.add('watched');
                if (icon) icon.className = 'fas fa-check-circle';
            } else {
                if (icon) icon.className = 'far fa-circle';
            }
        }

        // show/hide corresponding unwatch button
        const unwatchBtn = document.querySelector(`button.unwatch-btn[data-lesson-id="${lessonId}"]`);
        if (unwatchBtn) {
            if (isActivityId(lessonId)) {
                unwatchBtn.style.display = (activitiesState[lessonId] && activitiesState[lessonId].status === 'correct') ? 'inline-block' : 'none';
            } else {
                unwatchBtn.style.display = watchedState[lessonId] ? 'inline-block' : 'none';
            }
        }
    };

    const updateAllUI = () => {
        document.querySelectorAll('a[data-lesson-id]').forEach(a => updateItemUI(a.dataset.lessonId));
        updateGlobalProgress();
    };

    const updateGlobalProgress = () => {
        const anchors = Array.from(document.querySelectorAll('a[data-lesson-id]'));
        const total = anchors.length;
        let done = 0;
        const modules = new Set();
        anchors.forEach(a => {
            const id = a.dataset.lessonId;
            modules.add(id.split('-')[0]);
            if (isActivityId(id)) {
                if (activitiesState[id] && activitiesState[id].status === 'correct') done++;
            } else {
                if (watchedState[id]) done++;
            }
        });
        const totalModules = modules.size || 1;
        const completedModules = Array.from(document.querySelectorAll('.course-card')).reduce((acc, card) => {
            const links = Array.from(card.querySelectorAll('a[data-lesson-id]'));
            const allDone = links.every(l => {
                const id = l.dataset.lessonId;
                return isActivityId(id) ? (activitiesState[id] && activitiesState[id].status === 'correct') : !!watchedState[id];
            });
            return acc + (allDone ? 1 : 0);
        }, 0);

        const percent = total > 0 ? Math.round((done / total) * 100) : 0;
        const watchedCountEl = document.getElementById('global-watched-count');
        const modulesCountEl = document.getElementById('global-modules-count');
        const progressPercentEl = document.getElementById('global-progress-percent');
        if (watchedCountEl) watchedCountEl.textContent = `${done}`;
        if (modulesCountEl) modulesCountEl.textContent = `${completedModules}/${totalModules}`;
        if (progressPercentEl) progressPercentEl.textContent = `${percent}%`;

        // update per-module progress bars
        document.querySelectorAll('.course-card').forEach(card => {
            const moduleId = card.dataset.moduleId;
            const links = Array.from(card.querySelectorAll('a[data-lesson-id]'));
            const totalItems = links.length;
            let doneItems = 0;
            links.forEach(l => {
                const id = l.dataset.lessonId;
                if (isActivityId(id)) {
                    if (activitiesState[id] && activitiesState[id].status === 'correct') doneItems++;
                } else {
                    if (watchedState[id]) doneItems++;
                }
            });
            const pct = totalItems ? Math.round((doneItems / totalItems) * 100) : 0;
            const bar = document.getElementById(`progress-bar-${moduleId}`);
            const label = document.getElementById(`progress-label-${moduleId}`);
            if (bar) { bar.style.width = `${pct}%`; bar.classList.toggle('completed', pct === 100); }
            if (label) { label.textContent = `${pct}% concluído`; label.classList.toggle('completed', pct === 100); }
        });
    };

    // --- Validações heurísticas para atividades ---
    const validators = {
        '1-A1': (answer) => {
            const code = answer.toLowerCase();
            if (!/calcular_imc\s*\(/.test(code)) return { ok: false, message: "Defina função calcular_imc(peso, altura)." };
            if (!(/\*\*2/.test(code) || /altura\s*\*\s*altura/.test(code))) return { ok: false, message: "Use 'altura**2' ou 'altura * altura' no cálculo." };
            return { ok: true };
        },
        '1-A2': (answer) => {
            const code = answer.toLowerCase();
            if (!/inverter_string\s*\(/.test(code)) return { ok: false, message: "Defina função inverter_string(texto)." };
            if (/\[:\-1\]/.test(code) || /reversed\(/.test(code)) return { ok: true };
            return { ok: false, message: "Use slicing [::-1] ou reversed para inverter string." };
        },
        '2-A2': (answer) => {
            const code = answer.toLowerCase();
            if (!/contar_palavras\s*\(/.test(code)) return { ok: false, message: "Defina contar_palavras(texto)." };
            if (/\.split\(/.test(code) || /collections\.counter/.test(code)) return { ok: true };
            return { ok: false, message: "Use split() ou collections.Counter para contar palavras." };
        },
        '4-A1': (answer) => {
            const up = answer.toUpperCase();
            const hasSelect = /SELECT\b/.test(up);
            const hasUpdate = /UPDATE\b/.test(up);
            const missing = [];
            if (!hasSelect) missing.push('SELECT');
            if (!hasUpdate) missing.push('UPDATE');
            if (missing.length) return { ok: false, message: 'Falta: ' + missing.join(', ') };
            return { ok: true };
        },
        '6-A1': (answer) => {
            const code = answer.toLowerCase();
            if (!/def\s+(?:soma|somar)\s*\(/.test(code) && !/def\s+soma\s*\(/.test(code)) return { ok: false, message: "Crie função soma(a,b)." };
            return { ok: true };
        }
    };

    // --- Modais / Inputs ---
    const activityModal = document.getElementById('activity-modal');
    const activityTitleEl = document.getElementById('activity-modal-title');
    const activityDescEl = document.getElementById('activity-modal-description');
    const codeInput = document.getElementById('activity-code-input');
    const checkBtn = document.getElementById('check-activity-btn');
    const feedbackEl = document.getElementById('activity-feedback-output');
    const completeBtn = document.getElementById('complete-activity-btn');

    const videoModal = document.getElementById('video-modal');
    const videoTitleEl = document.getElementById('video-modal-title');
    const videoIframe = document.getElementById('video-iframe');
    const completeVideoBtn = document.getElementById('complete-video-btn');

    const openActivityModal = (title, desc, lessonId) => {
        currentLessonId = lessonId;
        activityTitleEl.textContent = title || 'Atividade';
        activityDescEl.textContent = desc || '';
        const st = activitiesState[lessonId];
        codeInput.value = st && st.answer ? st.answer : '';
        feedbackEl.className = 'activity-feedback-area';
        feedbackEl.textContent = st ? (st.status === 'correct' ? 'Atividade já corrigida: correta.' : (st.status === 'wrong' ? 'Envio anterior incorreto.' : 'Resposta pendente de correção.')) : 'O feedback do seu código aparecerá aqui.';
        activityModal.classList.add('open');
        if (st && st.status === 'correct') {
            completeBtn.classList.add('completed');
            completeBtn.textContent = 'Concluído';
        } else {
            completeBtn.classList.remove('completed');
            completeBtn.textContent = 'Marcar como Concluído (Se Correto)';
        }
    };

    const closeActivityModal = () => {
        activityModal.classList.remove('open');
        currentLessonId = null;
    };

    // fechar modais
    document.querySelectorAll('.modal-close-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const modalId = btn.dataset.modal;
            if (modalId === 'video-modal') {
                videoIframe.src = '';
                videoModal.classList.remove('open');
                currentLessonId = null;
            } else if (modalId === 'activity-modal') {
                closeActivityModal();
            } else {
                const el = document.getElementById(modalId);
                if (el) el.classList.remove('open');
            }
        });
    });

    // --- Delegação de cliques: abrir modais e desmarcar ---
    document.querySelector('.course-grid-wrapper').addEventListener('click', (e) => {
        const videoAnchor = e.target.closest('a.open-video-modal');
        if (videoAnchor) {
            e.preventDefault();

            // bloqueio por pagamento — trata cancelamento corretamente e impede outros handlers
            const lockedFlag = String(videoAnchor.dataset.locked || '').trim();
            const isLocked = (lockedFlag === '1' || lockedFlag === 'true');

            if (isLocked) {
                const go = confirm('Esta aula está bloqueada. Deseja ir para a página de pagamentos (R$29,99)?');
                if (go) {
                    window.location.href = '/pagamento';
                    return;
                }
                // usuário cancelou: garantir que nenhum handler anterior/seguinte abra a aula
                try { e.stopImmediatePropagation?.(); } catch (err) {}
                try { e.stopPropagation?.(); } catch (err) {}
                // fechar modal caso já tenha sido aberto por outro listener
                if (videoIframe) videoIframe.src = '';
                if (videoModal) videoModal.classList.remove('open');
                return;
            }

            const url = videoAnchor.dataset.videoUrl || '';
            const title = videoAnchor.dataset.videoTitle || '';
            const lessonId = videoAnchor.dataset.lessonId;
            currentLessonId = lessonId;
            // convert youtube formats
            let embed = url;
            try {
                if (url.includes('youtu.be/')) {
                    const id = url.split('youtu.be/')[1].split('?')[0];
                    embed = `https://www.youtube.com/embed/${id}`;
                } else if (url.includes('youtube.com/watch')) {
                    const v = new URL(url).searchParams.get('v');
                    if (v) embed = `https://www.youtube.com/embed/${v}`;
                } else if (url.includes('youtube.com/embed/')) {
                    embed = url;
                }
            } catch (err) { embed = url; }

            videoTitleEl.textContent = title;
            videoIframe.src = embed + '?autoplay=1&rel=0';
            videoModal.classList.add('open');
            if (watchedState[lessonId]) {
                completeVideoBtn.classList.add('completed');
                completeVideoBtn.textContent = 'Concluído';
            } else {
                completeVideoBtn.classList.remove('completed');
                completeVideoBtn.textContent = 'Marcar Aula como Concluída';
            }
            return;
        }


        const activityAnchor = e.target.closest('a.open-modal-activity');
        if (activityAnchor) {
            e.preventDefault();
            openActivityModal(activityAnchor.dataset.activityTitle, activityAnchor.dataset.activityDesc, activityAnchor.dataset.lessonId);
            return;
        }

        const unwatchBtn = e.target.closest('button.unwatch-btn');
        if (unwatchBtn) {
            const lessonId = unwatchBtn.dataset.lessonId;
            if (!lessonId) return;
            if (isActivityId(lessonId)) {
                delete activitiesState[lessonId];
                setActivitiesState(activitiesState);
            } else {
                delete watchedState[lessonId];
                setWatchedState(watchedState);
            }
            updateItemUI(lessonId);
            updateGlobalProgress();
            return;
        }
    });

    // botão "Corrigir Atividade"
    if (checkBtn) {
        checkBtn.addEventListener('click', () => {
            if (!currentLessonId) return;
            const answer = codeInput.value.trim();
            if (!answer) {
                feedbackEl.classList.add('feedback-failure');
                feedbackEl.textContent = 'Escreva algo antes de enviar para correção.';
                return;
            }
            const validator = validators[currentLessonId];
            if (validator) {
                const res = validator(answer);
                if (res.ok) {
                    activitiesState[currentLessonId] = { status: 'correct', answer };
                    setActivitiesState(activitiesState);
                    feedbackEl.classList.remove('feedback-failure');
                    feedbackEl.classList.add('feedback-success');
                    feedbackEl.textContent = 'Resposta correta — atividade marcada como correta.';
                    completeBtn.classList.add('completed');
                    completeBtn.textContent = 'Concluído';
                } else {
                    activitiesState[currentLessonId] = { status: 'wrong', answer };
                    setActivitiesState(activitiesState);
                    feedbackEl.classList.remove('feedback-success');
                    feedbackEl.classList.add('feedback-failure');
                    feedbackEl.textContent = `Resposta incorreta — ${res.message || 'Revise e tente novamente.'}`;
                    completeBtn.classList.remove('completed');
                    completeBtn.textContent = 'Reenviar para Correção';
                }
            } else {
                activitiesState[currentLessonId] = { status: 'pending', answer };
                setActivitiesState(activitiesState);
                feedbackEl.classList.remove('feedback-failure','feedback-success');
                feedbackEl.textContent = 'Resposta salva — pendente de correção manual.';
                completeBtn.classList.remove('completed');
                completeBtn.textContent = 'Enviar (Pendente)';
            }
            updateItemUI(currentLessonId);
            updateGlobalProgress();
        });
    }

    // marcar atividade como concluída (só se validação ok)
    if (completeBtn) {
        completeBtn.addEventListener('click', () => {
            if (!currentLessonId) return;
            const st = activitiesState[currentLessonId];
            if (st && st.status === 'correct') {
                updateItemUI(currentLessonId);
                updateGlobalProgress();
                setTimeout(closeActivityModal, 400);
                return;
            }
            feedbackEl.classList.add('feedback-failure');
            feedbackEl.textContent = 'A atividade não está correta. Use "CORRIGIR ATIVIDADE" antes de marcar como concluída.';
        });
    }

    // marcar vídeo como concluído
    if (completeVideoBtn) {
        completeVideoBtn.addEventListener('click', () => {
            if (!currentLessonId) return;
            if (!watchedState[currentLessonId]) {
                watchedState[currentLessonId] = true;
                setWatchedState(watchedState);
                updateItemUI(currentLessonId);
                updateGlobalProgress();
                completeVideoBtn.classList.add('completed');
                completeVideoBtn.textContent = 'Concluído';
                setTimeout(() => {
                    videoIframe.src = '';
                    videoModal.classList.remove('open');
                    currentLessonId = null;
                }, 500);
            }
        });
    }

    // --- PAGINAÇÃO ---
    const pages = Array.from(document.querySelectorAll('.course-grid.page'));
    const totalPages = pages.length || 1;
    let currentPage = 1;
    const prevBtn = document.getElementById('prev-page-btn');
    const nextBtn = document.getElementById('next-page-btn');
    const pageIndicator = document.getElementById('page-indicator');

    const showPage = (n) => {
        if (n < 1) n = 1;
        if (n > totalPages) n = totalPages;
        pages.forEach(p => p.classList.toggle('active-page', parseInt(p.dataset.page, 10) === n));
        currentPage = n;
        if (pageIndicator) pageIndicator.textContent = `Página ${currentPage} de ${totalPages}`;
        if (prevBtn) prevBtn.disabled = currentPage === 1;
        if (nextBtn) nextBtn.disabled = currentPage === totalPages;
        const topEl = document.querySelector('.container');
        if (topEl) topEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    };

    if (prevBtn) prevBtn.addEventListener('click', () => showPage(currentPage - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => showPage(currentPage + 1));
    showPage(1);

    // inicializa UI
    updateAllUI();

    // pequeno hook para botões sociais / dev login (se existirem)
    const g = document.getElementById('googleLogin');
    if (g) g.addEventListener('click', () => window.location.href = "/auth/google");
    const f = document.getElementById('facebookLogin');
    if (f) f.addEventListener('click', () => window.location.href = "/auth/facebook");
    const form = document.querySelector("form");
    if (form) {
        form.addEventListener("submit", function (e) {
            const usernameInput = form.querySelector("input[name='username']");
            const passwordInput = form.querySelector("input[name='password']");
            if (usernameInput && passwordInput) {
                const username = usernameInput.value;
                const password = passwordInput.value;
                if (username === "dev" && password === "dev") {
                    e.preventDefault();
                    window.location.href = "/login_dev";
                }
            }
        });
    }
});


document.addEventListener('DOMContentLoaded', () => {

    // --- Helpers para persistência ---
    const getWatchedState = () => {
        try { return JSON.parse(localStorage.getItem('courseWatchedState') || '{}'); } catch { return {}; }
    };
    const setWatchedState = (s) => localStorage.setItem('courseWatchedState', JSON.stringify(s));

    const getActivitiesState = () => {
        try { return JSON.parse(localStorage.getItem('courseActivitiesState') || '{}'); } catch { return {}; }
    };
    const setActivitiesState = (s) => localStorage.setItem('courseActivitiesState', JSON.stringify(s));

   const isCoursePaid = () => localStorage.getItem('course_paid') === '1';
    const markCoursePaid = () => { localStorage.setItem('course_paid','1'); window.dispatchEvent(new Event('course-paid')); };

    let watchedState = getWatchedState();
    let activitiesState = getActivitiesState();
    let currentLessonId = null;

    // ensure first lesson always unlocked
    const firstLessonId = '1-1';

    // --- Utilitários de UI ---
    const isActivityId = id => /-A/i.test(id);

    const updateItemUI = (lessonId) => {
        const anchor = document.querySelector(`a[data-lesson-id="${lessonId}"]`);
        if (!anchor) return;
        const icon = anchor.querySelector('.lesson-icon i');
        anchor.classList.remove('watched','wrong','pending');
        // lock handling
        const paid = isCoursePaid();
        const locked = (!paid && lessonId !== firstLessonId);
        // ensure lock icon exists
        let lockEl = anchor.querySelector('.lock-icon');
       if (!lockEl) {
           lockEl = document.createElement('span');
           lockEl.className = 'lock-icon';            anchor.appendChild(lockEl);
        }      lockEl.classList.toggle('locked', locked);
       lockEl.classList.toggle('unlocked', !locked);
        lockEl.title = locked ? 'Aula bloqueada. Pague R$29,99 para liberar.' : 'Aula liberada';
       lockEl.innerHTML = locked ? '<i class=\"fas fa-lock\"></i>' : '<i class=\"fas fa-unlock\"></i>';
        // visual pointer
        anchor.dataset.locked = locked ? '1' : '0';
        // hide unwatch if locked
        const unwatchBtn = document.querySelector(`button.unwatch-btn[data-lesson-id="${lessonId}"]`);
        if (unwatchBtn) unwatchBtn.style.display = locked ? 'none' : (isActivityId(lessonId) ? (activitiesState[lessonId] && activitiesState[lessonId].status === 'correct' ? 'inline-block' : 'none') : (watchedState[lessonId] ? 'inline-block' : 'none'));

        if (isActivityId(lessonId)) {
            const st = activitiesState[lessonId];
            if (st && st.status === 'correct') {
                anchor.classList.add('watched');
                if (icon) icon.className = 'fas fa-check-circle';
            } else if (st && st.status === 'wrong') {
                anchor.classList.add('wrong');
                if (icon) icon.className = 'fas fa-times-circle';
            } else if (st && st.status === 'pending') {
                anchor.classList.add('pending');
                if (icon) icon.className = 'fas fa-hourglass-half';
            } else {
                if (icon) icon.className = 'far fa-circle';
            }
        } else {
            if (watchedState[lessonId]) {
                anchor.classList.add('watched');
                if (icon) icon.className = 'fas fa-check-circle';
            } else {
                if (icon) icon.className = 'far fa-circle';
            }
        }
    };
    // listen for payment event (from payment page)
    window.addEventListener('course-paid', () => {
        // paid -> refresh UI
// +        updateAllUI();
        alert('Pagamento confirmado — todas as aulas liberadas.');
    });
    // also listen storage event (in case payment happens in new tab)
    window.addEventListener('storage', (ev) => {
       if (ev.key === 'course_paid' && ev.newValue === '1') {
            window.dispatchEvent(new Event('course-paid'));
        }
  });

    const updateAllUI = () => {
        document.querySelectorAll('a[data-lesson-id]').forEach(a => updateItemUI(a.dataset.lessonId));
        updateGlobalProgress();
    };

    // ...existing code...

    // --- Delegação de cliques: abrir modais e desmarcar ---
    document.querySelector('.course-grid-wrapper').addEventListener('click', (e) => {
        const videoAnchor = e.target.closest('a.open-video-modal');
        if (videoAnchor) {
            e.preventDefault();
        // bloqueio por pagamento
           if (videoAnchor.dataset.locked === '1') {
               if (confirm('Esta aula está bloqueada. Deseja ir para a página de pagamentos (R$29,99)?')) {
                  window.location.href = '/pagamento';
               }
             return;
           }
            const url = videoAnchor.dataset.videoUrl || '';
            const title = videoAnchor.dataset.videoTitle || '';
            const lessonId = videoAnchor.dataset.lessonId;
            currentLessonId = lessonId;
            // convert youtube formats
            let embed = url;
            try {
                if (url.includes('youtu.be/')) {
                    const id = url.split('youtu.be/')[1].split('?')[0];
                    embed = `https://www.youtube.com/embed/${id}`;
                } else if (url.includes('youtube.com/watch')) {
                    const v = new URL(url).searchParams.get('v');
                    if (v) embed = `https://www.youtube.com/embed/${v}`;
                } else if (url.includes('youtube.com/embed/')) {
                    embed = url;
                }
            } catch (err) { embed = url; }

            videoTitleEl.textContent = title;
            videoIframe.src = embed + '?autoplay=1&rel=0';
            videoModal.classList.add('open');
            if (watchedState[lessonId]) {
                completeVideoBtn.classList.add('completed');
                completeVideoBtn.textContent = 'Concluído';
            } else {
                completeVideoBtn.classList.remove('completed');
                completeVideoBtn.textContent = 'Marcar Aula como Concluída';
            }
            return;
        }

        const activityAnchor = e.target.closest('a.open-modal-activity');
        if (activityAnchor) {
            e.preventDefault();
           if (activityAnchor.dataset.locked === '1') {
              if (confirm('Esta atividade está bloqueada. Deseja ir para a página de pagamentos (R$29,99)?')) {
                 window.location.href = '/pagamento';
             }
               return;
           }
            openActivityModal(activityAnchor.dataset.activityTitle, activityAnchor.dataset.activityDesc, activityAnchor.dataset.lessonId);
            return;
        }

        const unwatchBtn = e.target.closest('button.unwatch-btn');
        if (unwatchBtn) {
            const lessonId = unwatchBtn.dataset.lessonId;
            if (!lessonId) return;
            if (isActivityId(lessonId)) {
                delete activitiesState[lessonId];
                setActivitiesState(activitiesState);
            } else {
                delete watchedState[lessonId];
                setWatchedState(watchedState);
            }
            updateItemUI(lessonId);
            updateGlobalProgress();
            return;
        }
    });

    // ...existing code...
    // inicializa UI
-   updateAllUI();
+   updateAllUI();
});
