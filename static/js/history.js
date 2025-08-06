// History page functionality

$(document).ready(function() {
    let currentPage = 1;
    let currentFilter = {};
    
    // Initialize
    loadSessions();
    
    // Event listeners
    $('#refreshBtn').on('click', function() {
        loadSessions();
    });
    
    $('#searchFilter').on('input', debounce(function() {
        currentFilter.search = $(this).val();
        currentPage = 1;
        loadSessions();
    }, 500));
    
    $('#statusFilter').on('change', function() {
        currentFilter.status = $(this).val();
        currentPage = 1;
        loadSessions();
    });
    
    // Load sessions from API
    function loadSessions() {
        showLoading();
        
        const params = new URLSearchParams({
            page: currentPage,
            per_page: 10
        });
        
        if (currentFilter.search) {
            params.append('search', currentFilter.search);
        }
        
        if (currentFilter.status) {
            params.append('status', currentFilter.status);
        }
        
        fetch(`/history?${params}`)
            .then(response => response.json())
            .then(data => {
                if (data.sessions && data.sessions.length > 0) {
                    displaySessions(data.sessions);
                    displayPagination(data.pagination);
                } else {
                    showEmptyState();
                }
            })
            .catch(error => {
                console.error('Error loading sessions:', error);
                showError('Erro ao carregar histórico');
            });
    }
    
    // Display sessions in the list
    function displaySessions(sessions) {
        const sessionsList = $('#sessionsList');
        const template = document.getElementById('sessionItemTemplate');
        
        sessionsList.empty();
        
        sessions.forEach(session => {
            const clone = template.content.cloneNode(true);
            const item = $(clone);
            
            // Fill session data
            item.find('.session-item').attr('data-session-id', session.id);
            item.find('.session-id').text(session.id.substring(0, 8) + '...');
            item.find('.session-date').text(formatDate(session.created_at));
            
            // Status badge
            const statusBadge = item.find('.session-status');
            statusBadge.text(getStatusText(session.status));
            statusBadge.addClass(getStatusClass(session.status));
            
            // Session info
            let filesInfo = [];
            if (session.has_transcription) filesInfo.push('Transcrição');
            if (session.screenshot_count > 0) filesInfo.push(`${session.screenshot_count} screenshots`);
            
            item.find('.session-files').html(`<i class="fas fa-file me-1"></i>${filesInfo.join(', ')}`);
            item.find('.session-actions').html(`<i class="fas fa-cogs me-1"></i>${session.actions_count || 0} ações`);
            item.find('.session-duration').html(`<i class="fas fa-clock me-1"></i>${session.processing_duration || 'N/A'}`);
            
            // Download menu
            const downloadMenu = item.find('.download-menu');
            if (session.has_transcription) {
                downloadMenu.append(`
                    <li><a class="dropdown-item download-link" href="#" data-session-id="${session.id}" data-file-type="transcription">
                        <i class="fas fa-file-text me-2"></i>Transcrição
                    </a></li>
                `);
            }
            
            if (session.has_documentation) {
                downloadMenu.append(`
                    <li><a class="dropdown-item download-link" href="#" data-session-id="${session.id}" data-file-type="documentation">
                        <i class="fas fa-file-alt me-2"></i>Documentação
                    </a></li>
                `);
            }
            
            for (let i = 0; i < session.screenshot_count; i++) {
                downloadMenu.append(`
                    <li><a class="dropdown-item download-link" href="#" data-session-id="${session.id}" data-file-type="screenshot_${i}">
                        <i class="fas fa-image me-2"></i>Screenshot ${i + 1}
                    </a></li>
                `);
            }
            
            if (downloadMenu.children().length === 0) {
                downloadMenu.append('<li><span class="dropdown-item text-muted">Nenhum arquivo disponível</span></li>');
            }
            
            sessionsList.append(item);
        });
        
        // Bind events
        bindSessionEvents();
        
        // Show sessions list
        hideLoading();
        $('#sessionsList').show();
        $('#emptyState').hide();
    }
    
    // Bind events to session items
    function bindSessionEvents() {
        $('.view-details-btn').off('click').on('click', function() {
            const sessionId = $(this).closest('.session-item').data('session-id');
            showSessionDetails(sessionId);
        });
        
        $('.download-link').off('click').on('click', function(e) {
            e.preventDefault();
            const sessionId = $(this).data('session-id');
            const fileType = $(this).data('file-type');
            downloadFile(sessionId, fileType);
        });
    }
    
    // Show session details modal
    function showSessionDetails(sessionId) {
        const modal = new bootstrap.Modal(document.getElementById('sessionModal'));
        const content = $('#sessionDetailsContent');
        
        // Show loading in modal
        content.html(`
            <div class="text-center p-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="mt-2">Carregando detalhes da sessão...</p>
            </div>
        `);
        
        modal.show();
        
        // Load session details
        fetch(`/history/${sessionId}`)
            .then(response => response.json())
            .then(session => {
                displaySessionDetails(session);
            })
            .catch(error => {
                console.error('Error loading session details:', error);
                content.html(`
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Erro ao carregar detalhes da sessão
                    </div>
                `);
            });
    }
    
    // Display session details in modal
    function displaySessionDetails(session) {
        const content = $('#sessionDetailsContent');
        
        let html = `
            <div class="row">
                <div class="col-md-6">
                    <h6><i class="fas fa-info-circle me-2"></i>Informações Gerais</h6>
                    <table class="table table-sm">
                        <tr><td><strong>ID:</strong></td><td><code>${session.id}</code></td></tr>
                        <tr><td><strong>Status:</strong></td><td><span class="badge ${getStatusClass(session.status)}">${getStatusText(session.status)}</span></td></tr>
                        <tr><td><strong>Criado em:</strong></td><td>${formatDate(session.created_at)}</td></tr>
                        <tr><td><strong>Atualizado em:</strong></td><td>${formatDate(session.updated_at)}</td></tr>
                        <tr><td><strong>Tempo de processamento:</strong></td><td>${session.processing_duration || 'N/A'}</td></tr>
                        <tr><td><strong>Modo:</strong></td><td>${session.transcription_only_mode ? 'Apenas transcrição' : 'Completo'}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6><i class="fas fa-chart-bar me-2"></i>Estatísticas</h6>
                    <table class="table table-sm">
                        <tr><td><strong>Arquivos processados:</strong></td><td>${session.files_count || 0}</td></tr>
                        <tr><td><strong>Ações extraídas:</strong></td><td>${session.actions_count || 0}</td></tr>
                        <tr><td><strong>Screenshots:</strong></td><td>${session.screenshot_count || 0}</td></tr>
                        <tr><td><strong>Documentação:</strong></td><td>${session.has_documentation ? '✅ Gerada' : '❌ Não gerada'}</td></tr>
                    </table>
                </div>
            </div>
        `;
        
        // Files section
        if (session.files && session.files.length > 0) {
            html += `
                <hr>
                <h6><i class="fas fa-folder me-2"></i>Arquivos</h6>
                <div class="row">
            `;
            
            session.files.forEach(file => {
                const icon = file.type === 'transcription' ? 'fa-file-text' : 'fa-image';
                const status = file.exists ? 'text-success' : 'text-danger';
                const statusIcon = file.exists ? 'fa-check' : 'fa-times';
                
                html += `
                    <div class="col-md-6 mb-2">
                        <div class="d-flex align-items-center">
                            <i class="fas ${icon} me-2"></i>
                            <span class="me-auto">${file.filename}</span>
                            <i class="fas ${statusIcon} ${status} ms-2"></i>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        // Logs section
        if (session.logs && session.logs.length > 0) {
            html += `
                <hr>
                <h6><i class="fas fa-list me-2"></i>Logs de Processamento</h6>
                <div class="logs-container" style="max-height: 300px; overflow-y: auto;">
            `;
            
            session.logs.forEach(log => {
                const levelClass = {
                    'INFO': 'text-info',
                    'WARNING': 'text-warning',
                    'ERROR': 'text-danger'
                }[log.level] || 'text-muted';
                
                html += `
                    <div class="log-entry mb-2 p-2 border-start border-3 ${levelClass.replace('text-', 'border-')} bg-light">
                        <div class="d-flex justify-content-between">
                            <span class="badge bg-secondary">${log.step}</span>
                            <small class="text-muted">${formatDate(log.timestamp)}</small>
                        </div>
                        <div class="mt-1">
                            <span class="badge ${levelClass.replace('text-', 'bg-')}">${log.level}</span>
                            <span class="ms-2">${log.message}</span>
                        </div>
                    </div>
                `;
            });
            
            html += '</div>';
        }
        
        // Error message
        if (session.error_message) {
            html += `
                <hr>
                <h6><i class="fas fa-exclamation-triangle me-2 text-danger"></i>Erro</h6>
                <div class="alert alert-danger">
                    ${session.error_message}
                </div>
            `;
        }
        
        content.html(html);
    }
    
    // Download file
    function downloadFile(sessionId, fileType) {
        const downloadUrl = `/download/${sessionId}/${fileType}`;
        
        // Create temporary link and click it
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    // Display pagination
    function displayPagination(pagination) {
        const nav = $('#paginationNav');
        nav.empty();
        
        if (pagination.pages <= 1) {
            return;
        }
        
        // Previous button
        if (pagination.has_prev) {
            nav.append(`
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${pagination.page - 1}">
                        <i class="fas fa-chevron-left"></i>
                    </a>
                </li>
            `);
        }
        
        // Page numbers
        const startPage = Math.max(1, pagination.page - 2);
        const endPage = Math.min(pagination.pages, pagination.page + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === pagination.page ? 'active' : '';
            nav.append(`
                <li class="page-item ${activeClass}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `);
        }
        
        // Next button
        if (pagination.has_next) {
            nav.append(`
                <li class="page-item">
                    <a class="page-link" href="#" data-page="${pagination.page + 1}">
                        <i class="fas fa-chevron-right"></i>
                    </a>
                </li>
            `);
        }
        
        // Bind pagination events
        nav.find('a').on('click', function(e) {
            e.preventDefault();
            const page = parseInt($(this).data('page'));
            if (page && page !== currentPage) {
                currentPage = page;
                loadSessions();
            }
        });
    }
    
    // Utility functions
    function showLoading() {
        $('#loadingState').show();
        $('#sessionsList').hide();
        $('#emptyState').hide();
    }
    
    function hideLoading() {
        $('#loadingState').hide();
    }
    
    function showEmptyState() {
        hideLoading();
        $('#sessionsList').hide();
        $('#emptyState').show();
    }
    
    function showError(message) {
        hideLoading();
        $('#sessionsList').html(`
            <div class="alert alert-danger m-3">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${message}
            </div>
        `).show();
    }
    
    function getStatusText(status) {
        const statusMap = {
            'uploading': 'Upload',
            'processing': 'Processando',
            'completed': 'Concluído',
            'error': 'Erro'
        };
        return statusMap[status] || status;
    }
    
    function getStatusClass(status) {
        const classMap = {
            'uploading': 'bg-info text-white',
            'processing': 'bg-warning text-dark',
            'completed': 'bg-success text-white',
            'error': 'bg-danger text-white'
        };
        return classMap[status] || 'bg-secondary text-white';
    }
    
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        const date = new Date(dateString);
        return date.toLocaleString('pt-BR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});