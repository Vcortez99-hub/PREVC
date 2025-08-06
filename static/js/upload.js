// Upload functionality for MVP RPA Documentation

$(document).ready(function() {
    let selectedFiles = {
        transcription: null,
        screenshots: []
    };

    // File input change handlers
    $('#transcription').on('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            if (FileHandler.validateFile(file, ['txt', 'vtt'])) {
                if (FileHandler.validateSize(file, 10 * 1024 * 1024)) { // 10MB
                    selectedFiles.transcription = file;
                    updateFileList();
                } else {
                    Utils.showToast('Arquivo de transcrição muito grande (máximo 10MB)', 'warning');
                    $(this).val('');
                }
            } else {
                Utils.showToast('Formato de transcrição não suportado', 'warning');
                $(this).val('');
            }
        }
    });

    // Checkbox for transcription-only mode
    $('#transcriptionOnlyMode').on('change', function() {
        const isChecked = $(this).is(':checked');
        const screenshotsSection = $('#screenshotsSection');
        const screenshotsInput = $('#screenshots');
        
        if (isChecked) {
            // Hide screenshots section and make it optional
            screenshotsSection.slideUp();
            screenshotsInput.prop('required', false);
            
            // Clear selected screenshots
            selectedFiles.screenshots = [];
            screenshotsInput.val('');
            
            // Update drag-drop zone text
            $('#dragDropZone .drag-drop-content p').html('<strong>Arraste transcrição aqui</strong> ou use o campo acima');
            $('#dragDropZone .drag-drop-content small').text('Apenas transcrições (.txt, .vtt)');
            
            // Update OCR step text to indicate it will be skipped
            $('#step-ocr span').text('Análise de screenshots (PULADO - modo só transcrição)');
            $('#step-ocr i').removeClass('fa-circle').addClass('fa-minus-circle text-muted');
            
            Utils.showToast('Modo apenas transcrição ativado', 'info');
        } else {
            // Show screenshots section and make it required again
            screenshotsSection.slideDown();
            screenshotsInput.prop('required', true);
            
            // Restore drag-drop zone text
            $('#dragDropZone .drag-drop-content p').html('<strong>Arraste arquivos aqui</strong> ou use os campos acima');
            $('#dragDropZone .drag-drop-content small').text('Transcrições (.txt, .vtt) e Screenshots (.png, .jpg)');
            
            // Restore OCR step text
            $('#step-ocr span').text('Análise de screenshots (OCR)');
            $('#step-ocr i').removeClass('fa-minus-circle text-muted').addClass('fa-circle');
            
            Utils.showToast('Screenshots obrigatórios novamente', 'info');
        }
        
        updateFileList();
    });

    $('#screenshots').on('change', function(e) {
        const files = Array.from(e.target.files);
        const validFiles = [];
        let totalSize = 0;

        files.forEach(file => {
            if (FileHandler.validateFile(file, ['png', 'jpg', 'jpeg', 'gif', 'bmp'])) {
                totalSize += file.size;
                validFiles.push(file);
            } else {
                Utils.showToast(`Formato não suportado: ${file.name}`, 'warning');
            }
        });

        if (totalSize > 40 * 1024 * 1024) { // 40MB
            Utils.showToast('Total de screenshots muito grande (máximo 40MB)', 'warning');
            $(this).val('');
            return;
        }

        selectedFiles.screenshots = validFiles;
        updateFileList();
    });

    // Drag and drop functionality
    const dragDropZone = $('#dragDropZone');

    dragDropZone.on('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).addClass('drag-over');
    });

    dragDropZone.on('dragleave', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('drag-over');
    });

    dragDropZone.on('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        $(this).removeClass('drag-over');

        const files = Array.from(e.originalEvent.dataTransfer.files);
        processDraggedFiles(files);
    });

    // Click to open file dialog
    dragDropZone.on('click', function() {
        // Determine which input to trigger based on current files
        if (!selectedFiles.transcription) {
            $('#transcription').click();
        } else {
            $('#screenshots').click();
        }
    });

    // Form submission
    $('#uploadForm').on('submit', function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            return;
        }

        uploadFiles();
    });

    // File removal
    $(document).on('click', '.file-remove', function() {
        const filename = $(this).closest('.file-item').data('filename');
        removeFile(filename);
    });

    function processDraggedFiles(files) {
        files.forEach(file => {
            const extension = file.name.split('.').pop().toLowerCase();
            
            if (['txt', 'vtt'].includes(extension)) {
                if (!selectedFiles.transcription) {
                    if (FileHandler.validateSize(file, 10 * 1024 * 1024)) {
                        selectedFiles.transcription = file;
                        // Update the file input
                        const dt = new DataTransfer();
                        dt.items.add(file);
                        document.getElementById('transcription').files = dt.files;
                    } else {
                        Utils.showToast('Arquivo de transcrição muito grande', 'warning');
                    }
                } else {
                    Utils.showToast('Apenas um arquivo de transcrição é permitido', 'warning');
                }
            } else if (['png', 'jpg', 'jpeg', 'gif', 'bmp'].includes(extension)) {
                selectedFiles.screenshots.push(file);
            } else {
                Utils.showToast(`Formato não suportado: ${file.name}`, 'warning');
            }
        });

        // Update screenshots input
        if (selectedFiles.screenshots.length > 0) {
            const dt = new DataTransfer();
            selectedFiles.screenshots.forEach(file => dt.items.add(file));
            document.getElementById('screenshots').files = dt.files;
        }

        updateFileList();
    }

    function updateFileList() {
        const fileListContent = $('#fileListContent');
        const fileList = $('#fileList');
        
        fileListContent.empty();
        
        let hasFiles = false;

        // Add transcription file
        if (selectedFiles.transcription) {
            const preview = FileHandler.createFilePreview(selectedFiles.transcription);
            fileListContent.append(preview);
            hasFiles = true;
        }

        // Add screenshot files
        selectedFiles.screenshots.forEach(file => {
            const preview = FileHandler.createFilePreview(file);
            fileListContent.append(preview);
            hasFiles = true;
        });

        // Show/hide file list
        if (hasFiles) {
            fileList.show();
        } else {
            fileList.hide();
        }

        // Update form validation
        updateFormValidation();
    }

    function removeFile(filename) {
        if (selectedFiles.transcription && selectedFiles.transcription.name === filename) {
            selectedFiles.transcription = null;
            $('#transcription').val('');
        }

        selectedFiles.screenshots = selectedFiles.screenshots.filter(file => file.name !== filename);
        
        // Update screenshots input
        const dt = new DataTransfer();
        selectedFiles.screenshots.forEach(file => dt.items.add(file));
        document.getElementById('screenshots').files = dt.files;

        updateFileList();
    }

    function validateForm() {
        const transcriptionOnlyMode = $('#transcriptionOnlyMode').is(':checked');
        
        if (!selectedFiles.transcription) {
            Utils.showToast('Arquivo de transcrição é obrigatório', 'warning');
            return false;
        }
        
        if (!transcriptionOnlyMode && selectedFiles.screenshots.length === 0) {
            Utils.showToast('Screenshots são obrigatórios (ou marque a opção "apenas transcrição")', 'warning');
            return false;
        }

        return true;
    }

    function updateFormValidation() {
        const uploadBtn = $('#uploadBtn');
        const transcriptionOnlyMode = $('#transcriptionOnlyMode').is(':checked');
        
        // Check if form is valid
        let isValid = false;
        
        if (transcriptionOnlyMode) {
            // Only transcription required
            isValid = selectedFiles.transcription !== null;
        } else {
            // Both transcription and screenshots required
            isValid = selectedFiles.transcription !== null && selectedFiles.screenshots.length > 0;
        }
        
        uploadBtn.prop('disabled', !isValid);
        
        if (isValid) {
            uploadBtn.removeClass('btn-secondary').addClass('btn-primary');
        } else {
            uploadBtn.removeClass('btn-primary').addClass('btn-secondary');
        }
    }

    function uploadFiles() {
        const formData = new FormData();
        const uploadBtn = $('#uploadBtn');
        const transcriptionOnlyMode = $('#transcriptionOnlyMode').is(':checked');
        
        // Disable form
        $('#uploadForm input').prop('disabled', true);
        uploadBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Enviando...');
        
        // Add files to form data
        if (selectedFiles.transcription) {
            formData.append('transcription', selectedFiles.transcription);
        }
        
        // Only add screenshots if not in transcription-only mode
        if (!transcriptionOnlyMode) {
            selectedFiles.screenshots.forEach(file => {
                formData.append('screenshots', file);
            });
        }
        
        // Add transcription-only mode flag
        formData.append('transcription_only_mode', transcriptionOnlyMode);
        
        // Add AI configuration
        formData.append('aiProvider', $('#aiProvider').val());
        formData.append('aiModel', $('#aiModel').val());
        formData.append('agentType', $('#agentType').val());
        formData.append('aiToken', $('#aiToken').val());

        // Show progress section
        $('#progressSection').slideDown();
        SessionManager.updateProgress(10, 'Enviando arquivos...');

        // Upload files
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            Utils.showToast('Arquivos enviados com sucesso!', 'success');
            window.APP.currentSessionId = data.session_id;
            
            // Update progress
            SessionManager.updateProgress(20, 'Upload concluído');
            
            // Start processing
            startProcessing(data.session_id);
            
            // Hide upload form
            $('#uploadForm').parent().slideUp();
        })
        .catch(error => {
            console.error('Upload error:', error);
            Utils.showToast('Erro no upload. Tente novamente.', 'danger');
            
            // Re-enable form
            $('#uploadForm input').prop('disabled', false);
            uploadBtn.prop('disabled', false).html('<i class="fas fa-rocket me-2"></i>Processar Arquivos');
            
            // Hide progress section
            $('#progressSection').slideUp();
        });
    }

    function startProcessing(sessionId) {
        fetch(`/process/${sessionId}`, {
            method: 'POST'
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            Utils.showToast('Processamento iniciado', 'info');
            
            // Start polling for status
            SessionManager.startPolling(sessionId);
            
            // Update progress
            SessionManager.updateProgress(30, 'Processando dados...');
            
            window.APP.isProcessing = true;
        })
        .catch(error => {
            console.error('Processing error:', error);
            Utils.showToast('Erro ao iniciar processamento', 'danger');
            
            // Re-enable form
            $('#uploadForm input').prop('disabled', false);
            $('#uploadBtn').prop('disabled', false).html('<i class="fas fa-rocket me-2"></i>Processar Arquivos');
            
            // Hide progress section
            $('#progressSection').slideUp();
        });
    }

    // Cancel processing
    $('#cancelBtn').on('click', function() {
        if (confirm('Tem certeza que deseja cancelar o processamento?')) {
            SessionManager.stopPolling();
            window.APP.isProcessing = false;
            
            // Reset form
            $('#uploadForm input').prop('disabled', false);
            $('#uploadBtn').prop('disabled', false).html('<i class="fas fa-rocket me-2"></i>Processar Arquivos');
            
            // Show upload form again
            $('#uploadForm').parent().slideDown();
            $('#progressSection').slideUp();
            
            Utils.showToast('Processamento cancelado', 'info');
        }
    });

    // Toggle token visibility
    $('#toggleToken').on('click', function() {
        const tokenInput = $('#aiToken');
        const icon = $(this).find('i');
        
        if (tokenInput.attr('type') === 'password') {
            tokenInput.attr('type', 'text');
            icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            tokenInput.attr('type', 'password');
            icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });
    
    // AI Provider change handler to update available models
    $('#aiProvider').on('change', function() {
        const provider = $(this).val();
        updateModelOptions(provider);
    });
    
    // Initialize form state
    updateFormValidation();
    
    // Show cancel button when processing
    $(document).on('APP:processingStarted', function() {
        $('#cancelBtn').show();
    });
    
    function updateModelOptions(provider) {
        const modelSelect = $('#aiModel');
        modelSelect.empty();
        
        const modelsByProvider = {
            'openai': [
                { value: 'gpt-4', text: 'GPT-4' },
                { value: 'gpt-4-turbo', text: 'GPT-4 Turbo' },
                { value: 'gpt-3.5-turbo', text: 'GPT-3.5 Turbo' }
            ],
            'azure': [
                { value: 'gpt-4', text: 'Azure GPT-4' },
                { value: 'gpt-35-turbo', text: 'Azure GPT-3.5 Turbo' }
            ],
            'anthropic': [
                { value: 'claude-3-opus', text: 'Claude 3 Opus' },
                { value: 'claude-3-sonnet', text: 'Claude 3 Sonnet' },
                { value: 'claude-3-haiku', text: 'Claude 3 Haiku' }
            ],
            'google': [
                { value: 'gemini-pro', text: 'Gemini Pro' },
                { value: 'gemini-pro-vision', text: 'Gemini Pro Vision' }
            ]
        };
        
        const models = modelsByProvider[provider] || [];
        models.forEach(model => {
            modelSelect.append(`<option value="${model.value}">${model.text}</option>`);
        });
        
        // Select first model by default
        if (models.length > 0) {
            modelSelect.val(models[0].value);
        }
    }
    
    // Initialize with default provider
    updateModelOptions($('#aiProvider').val());
});

// Export for use in other scripts
window.UploadHandler = {
    reset: function() {
        $('#uploadForm')[0].reset();
        $('#fileList').hide();
        $('#fileListContent').empty();
        $('#progressSection').hide();
        $('#resultSection').hide();
        $('#uploadForm').parent().show();
        
        selectedFiles = {
            transcription: null,
            screenshots: []
        };
    }
};