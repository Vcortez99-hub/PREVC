// Review functionality for MVP RPA Documentation

$(document).ready(function() {
    let currentSessionId = null;
    let documentationContent = '';
    let isEditMode = false;

    // Initialize if session data is available
    if (typeof window.sessionData !== 'undefined') {
        currentSessionId = window.sessionData.id;
        initializeReviewPage();
    }

    function initializeReviewPage() {
        loadSessionResult();
        setupEventHandlers();
    }

    function setupEventHandlers() {
        // Edit/Preview toggle
        $('#editBtn').on('click', function() {
            if (!isEditMode) {
                enterEditMode();
            }
        });

        $('#previewBtn').on('click', function() {
            if (isEditMode) {
                exitEditMode();
            }
        });

        // Save changes
        $('#saveBtn').on('click', function() {
            saveChanges();
        });

        // Approve/Reject buttons
        $('#approveBtn').on('click', function() {
            $('#approveModal').modal('show');
        });

        $('#rejectBtn').on('click', function() {
            $('#rejectModal').modal('show');
        });

        // Modal confirmations
        $('#confirmApproveBtn').on('click', function() {
            approveDocumentation();
        });

        $('#confirmRejectBtn').on('click', function() {
            rejectDocumentation();
        });

        // Download buttons
        $('#downloadWordBtn').on('click', function() {
            downloadDocument('docx');
        });

        $('#downloadMarkdownBtn').on('click', function() {
            downloadDocument('markdown');
        });

        // New process button
        $('#newProcessBtn').on('click', function() {
            if (confirm('Iniciar novo processo? Você será redirecionado para a página inicial.')) {
                window.location.href = '/';
            }
        });

        // Screenshot click handler
        $(document).on('click', '.screenshot-thumbnail', function() {
            const imageSrc = $(this).attr('src');
            $('#modalImage').attr('src', imageSrc);
            $('#imageModal').modal('show');
        });
    }

    async function loadSessionResult() {
        try {
            Utils.showLoading($('#documentationContent'), 'Carregando documentação...');
            Utils.showLoading($('#transcriptionPreview'), 'Carregando transcrição...');
            Utils.showLoading($('#screenshotsPreview'), 'Carregando screenshots...');

            const response = await fetch(`/result/${currentSessionId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            
            displayDocumentation(data.documentation);
            displayTranscription(data.actions);
            displayScreenshots();
            displayProcessingStats(data);

        } catch (error) {
            console.error('Error loading session result:', error);
            Utils.showError($('#documentationContent'), 'Erro ao carregar documentação');
            Utils.showError($('#transcriptionPreview'), 'Erro ao carregar transcrição');
            Utils.showError($('#screenshotsPreview'), 'Erro ao carregar screenshots');
        }
    }

    function displayDocumentation(content) {
        documentationContent = content || 'Documentação não disponível';
        
        // Convert markdown to HTML for display
        const htmlContent = marked ? marked.parse(documentationContent) : documentationContent.replace(/\n/g, '<br>');
        
        $('#documentationContent').html(htmlContent);
        $('#documentationEditor').val(documentationContent);
    }

    function displayTranscription(actions) {
        if (!actions || actions.length === 0) {
            $('#transcriptionPreview').html('<p class="text-muted">Nenhuma ação identificada</p>');
            return;
        }

        let transcriptionHtml = '<div class="action-list">';
        
        actions.forEach((action, index) => {
            const confidenceClass = action.confidence >= 0.8 ? 'success' : 
                                  action.confidence >= 0.5 ? 'warning' : 'danger';
            
            transcriptionHtml += `
                <div class="action-item mb-2 p-2 border rounded">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${index + 1}. ${action.action_type.toUpperCase()}</strong>
                            <span class="text-primary">"${action.element}"</span>
                        </div>
                        <span class="badge bg-${confidenceClass}">${Math.round(action.confidence * 100)}%</span>
                    </div>
                    <small class="text-muted">
                        <i class="fas fa-user me-1"></i>${action.speaker} 
                        <i class="fas fa-clock ms-2 me-1"></i>${action.timestamp}
                    </small>
                </div>
            `;
        });
        
        transcriptionHtml += '</div>';
        $('#transcriptionPreview').html(transcriptionHtml);
        
        // Update actions count
        $('#actionsCount').text(actions.length);
    }

    function displayScreenshots() {
        // Get screenshot files from session data
        const screenshotFiles = window.sessionData.screenshot_files || [];
        
        if (screenshotFiles.length === 0) {
            $('#screenshotsPreview').html('<p class="text-muted">Nenhum screenshot disponível</p>');
            return;
        }

        let screenshotsHtml = '<div class="row g-2">';
        
        screenshotFiles.forEach((file, index) => {
            // Note: In a real implementation, you'd need an endpoint to serve these images
            // For MVP, we'll show placeholders
            screenshotsHtml += `
                <div class="col-6 col-md-4">
                    <div class="screenshot-item">
                        <div class="screenshot-placeholder bg-light border rounded d-flex align-items-center justify-content-center" 
                             style="height: 80px; cursor: pointer;" 
                             title="Screenshot ${index + 1}">
                            <i class="fas fa-image fa-2x text-muted"></i>
                        </div>
                        <div class="screenshot-info">
                            <small>Screenshot ${index + 1}</small>
                        </div>
                    </div>
                </div>
            `;
        });
        
        screenshotsHtml += '</div>';
        $('#screenshotsPreview').html(screenshotsHtml);
        
        // Update screenshot count
        $('#screenshotCount').text(`${screenshotFiles.length} screenshot${screenshotFiles.length !== 1 ? 's' : ''}`);
    }

    function displayProcessingStats(data) {
        // Calculate correlation quality
        const totalActions = data.actions ? data.actions.length : 0;
        const avgConfidence = totalActions > 0 ? 
            data.actions.reduce((sum, action) => sum + action.confidence, 0) / totalActions : 0;
        
        $('#correlationQuality').text(`${Math.round(avgConfidence * 100)}%`);
        
        // Show processing stats section
        $('#processingStats').show();
    }

    function enterEditMode() {
        $('#documentationView').hide();
        $('#documentationEdit').show();
        $('#editBtn').hide();
        $('#previewBtn').show();
        $('#saveBtn').show();
        
        isEditMode = true;
        
        // Focus on editor
        $('#documentationEditor').focus();
    }

    function exitEditMode() {
        // Get current editor content
        const editorContent = $('#documentationEditor').val();
        
        // Convert to HTML and display
        const htmlContent = marked ? marked.parse(editorContent) : editorContent.replace(/\n/g, '<br>');
        $('#documentationContent').html(htmlContent);
        
        $('#documentationEdit').hide();
        $('#documentationView').show();
        $('#previewBtn').hide();
        $('#editBtn').show();
        $('#saveBtn').hide();
        
        isEditMode = false;
        
        // Update stored content
        documentationContent = editorContent;
    }

    function saveChanges() {
        const editorContent = $('#documentationEditor').val();
        
        // In a real implementation, you'd save to the server here
        // For MVP, we'll just update the local content
        documentationContent = editorContent;
        
        Utils.showToast('Alterações salvas', 'success');
        
        // Update button state
        $('#saveBtn').prop('disabled', true).text('Salvo');
        setTimeout(() => {
            $('#saveBtn').prop('disabled', false).html('<i class="fas fa-save me-2"></i>Salvar Alterações');
        }, 2000);
    }

    function approveDocumentation() {
        // In a real implementation, you'd update the session status
        $('#approveModal').modal('hide');
        
        Utils.showToast('Documentação aprovada com sucesso!', 'success');
        
        // Disable approve/reject buttons
        $('#approveBtn').prop('disabled', true).html('<i class="fas fa-check me-2"></i>Aprovado');
        $('#rejectBtn').prop('disabled', true);
        
        // Update final status badge
        $('#finalStatus').removeClass('bg-success').addClass('bg-primary').text('Aprovado');
    }

    function rejectDocumentation() {
        const reason = $('#rejectionReason').val();
        
        // In a real implementation, you'd update the session status and store the reason
        $('#rejectModal').modal('hide');
        
        Utils.showToast('Documentação rejeitada', 'warning');
        
        // Update status
        $('#finalStatus').removeClass('bg-success').addClass('bg-danger').text('Rejeitado');
        
        console.log('Rejection reason:', reason);
    }

    function downloadDocument(format) {
        try {
            if (format === 'docx') {
                // Download Word document
                const link = document.createElement('a');
                link.href = `/export/${currentSessionId}/docx`;
                link.download = `documentacao_rpa_${currentSessionId.substring(0, 8)}.docx`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                Utils.showToast('Download iniciado', 'info');
            } else if (format === 'markdown') {
                // Download markdown as text file
                const blob = new Blob([documentationContent], { type: 'text/markdown' });
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = `documentacao_rpa_${currentSessionId.substring(0, 8)}.md`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(url);
                
                Utils.showToast('Download markdown concluído', 'success');
            }
        } catch (error) {
            console.error('Download error:', error);
            Utils.showToast('Erro no download', 'danger');
        }
    }

    // Auto-save functionality for editor
    let saveTimeout;
    $('#documentationEditor').on('input', function() {
        // Clear previous timeout
        if (saveTimeout) {
            clearTimeout(saveTimeout);
        }
        
        // Set new timeout for auto-save
        saveTimeout = setTimeout(() => {
            if (isEditMode) {
                saveChanges();
            }
        }, 3000); // Auto-save after 3 seconds of inactivity
    });

    // Export for external use
    window.ReviewHandler = {
        getCurrentContent: function() {
            return documentationContent;
        },
        
        setContent: function(content) {
            documentationContent = content;
            displayDocumentation(content);
        },
        
        isInEditMode: function() {
            return isEditMode;
        }
    };
});

// Add marked.js for markdown parsing (CDN)
if (typeof marked === 'undefined') {
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    document.head.appendChild(script);
}