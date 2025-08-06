// MVP RPA Documentation - Main JavaScript

// Global variables
window.APP = {
    currentSessionId: null,
    pollingInterval: null,
    isProcessing: false
};

// Utility functions
const Utils = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Format timestamp
    formatTimestamp: function(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('pt-BR');
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast element
        const toast = $(`
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `);

        // Add to toast container (create if doesn't exist)
        let toastContainer = $('#toastContainer');
        if (toastContainer.length === 0) {
            toastContainer = $('<div id="toastContainer" class="toast-container position-fixed top-0 end-0 p-3"></div>');
            $('body').append(toastContainer);
        }

        toastContainer.append(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();

        // Remove from DOM after hiding
        toast.on('hidden.bs.toast', function() {
            $(this).remove();
        });
    },

    // Show loading state
    showLoading: function(element, text = 'Carregando...') {
        element.html(`
            <div class="text-center py-3">
                <div class="spinner-border text-primary" role="status" style="width: 2rem; height: 2rem;">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2 text-muted">${text}</p>
            </div>
        `);
    },

    // Show error state
    showError: function(element, message = 'Erro ao carregar dados') {
        element.html(`
            <div class="text-center py-3">
                <i class="fas fa-exclamation-triangle fa-2x text-danger mb-2"></i>
                <p class="text-danger">${message}</p>
                <button class="btn btn-outline-primary btn-sm" onclick="location.reload()">
                    Recarregar
                </button>
            </div>
        `);
    },

    // Make API request with error handling
    apiRequest: function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        return fetch(url, finalOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('API Request Error:', error);
                throw error;
            });
    }
};

// Session management
const SessionManager = {
    // Start polling for session status
    startPolling: function(sessionId) {
        if (window.APP.pollingInterval) {
            clearInterval(window.APP.pollingInterval);
        }

        window.APP.pollingInterval = setInterval(() => {
            this.checkStatus(sessionId);
        }, 2000);
    },

    // Stop polling
    stopPolling: function() {
        if (window.APP.pollingInterval) {
            clearInterval(window.APP.pollingInterval);
            window.APP.pollingInterval = null;
        }
    },

    // Check session status
    checkStatus: function(sessionId) {
        Utils.apiRequest(`/status/${sessionId}`)
            .then(data => {
                this.handleStatusUpdate(data);
            })
            .catch(error => {
                console.error('Error checking status:', error);
                Utils.showToast('Erro ao verificar status', 'danger');
            });
    },

    // Handle status update
    handleStatusUpdate: function(data) {
        const status = data.status;
        
        // Update progress based on status
        if (status === 'uploading') {
            this.updateProgress(20, 'Upload concluído');
        } else if (status === 'processing') {
            this.updateProgress(60, 'Processando dados...');
        } else if (status === 'completed') {
            this.updateProgress(100, 'Processamento concluído!');
            this.onProcessingComplete(data);
        } else if (status === 'error') {
            this.onProcessingError(data);
        }
    },

    // Update progress bar
    updateProgress: function(percent, text) {
        const progressBar = $('#progressBar');
        const statusText = $('#statusText');

        progressBar.css('width', percent + '%');
        progressBar.text(percent + '%');
        statusText.text(text);

        // Update step indicators
        this.updateStepIndicators(percent);
    },

    // Update step indicators
    updateStepIndicators: function(percent) {
        const steps = [
            { id: 'step-upload', threshold: 20 },
            { id: 'step-transcription', threshold: 35 },
            { id: 'step-ocr', threshold: 50 },
            { id: 'step-correlation', threshold: 65 },
            { id: 'step-ai', threshold: 80 },
            { id: 'step-complete', threshold: 100 }
        ];

        steps.forEach(step => {
            const element = $(`#${step.id}`);
            const icon = element.find('i');

            if (percent >= step.threshold) {
                element.removeClass('current').addClass('completed');
                icon.removeClass('fa-circle fa-circle-notch fa-spin')
                    .addClass('fa-check-circle')
                    .css('color', '#28a745');
            } else if (percent >= step.threshold - 15) {
                element.removeClass('completed').addClass('current');
                icon.removeClass('fa-circle fa-check-circle')
                    .addClass('fa-circle-notch fa-spin')
                    .css('color', '#007bff');
            }
        });
    },

    // Handle processing completion
    onProcessingComplete: function(data) {
        this.stopPolling();
        
        // Hide progress section
        $('#progressSection').slideUp();
        
        // Show result section
        $('#resultSection').slideDown();
        $('#sessionId').text(data.session_id.substring(0, 8));
        
        // Setup download buttons
        this.setupDownloadButtons(data.session_id);
        
        // Show success toast
        Utils.showToast('Documentação gerada com sucesso!', 'success');
    },

    // Handle processing error
    onProcessingError: function(data) {
        this.stopPolling();
        
        // Update progress bar to error state
        const progressBar = $('#progressBar');
        progressBar.removeClass('progress-bar-striped progress-bar-animated')
                  .addClass('bg-danger');
        $('#statusText').text('Erro no processamento');
        
        // Show error message
        Utils.showToast('Erro durante o processamento. Tente novamente.', 'danger');
        
        // Enable upload form again
        $('#uploadForm input').prop('disabled', false);
        $('#uploadBtn').prop('disabled', false).text('Processar Arquivos');
    },

    // Setup download buttons
    setupDownloadButtons: function(sessionId) {
        $('#reviewBtn').off('click').on('click', function() {
            window.location.href = `/review/${sessionId}`;
        });

        $('#downloadBtn').off('click').on('click', function() {
            window.location.href = `/export/${sessionId}/docx`;
        });
    }
};

// File handling
const FileHandler = {
    // Validate file type
    validateFile: function(file, allowedTypes) {
        const extension = file.name.split('.').pop().toLowerCase();
        return allowedTypes.includes(extension);
    },

    // Validate file size
    validateSize: function(file, maxSize) {
        return file.size <= maxSize;
    },

    // Create file preview element
    createFilePreview: function(file) {
        const isImage = file.type.startsWith('image/');
        const icon = isImage ? 'fa-image' : 'fa-file-text';
        
        return $(`
            <div class="file-item" data-filename="${file.name}">
                <div class="file-icon">
                    <i class="fas ${icon} text-primary"></i>
                </div>
                <div class="file-info">
                    <div class="file-name">${file.name}</div>
                    <div class="file-size">${Utils.formatFileSize(file.size)}</div>
                </div>
                <div class="file-remove" title="Remover arquivo">
                    <i class="fas fa-times"></i>
                </div>
            </div>
        `);
    }
};

// Initialize application
$(document).ready(function() {
    console.log('MVP RPA Documentation App initialized');
    
    // Setup global error handling
    window.addEventListener('error', function(e) {
        console.error('Global error:', e.error);
        Utils.showToast('Erro inesperado na aplicação', 'danger');
    });
    
    // Setup unhandled promise rejection handling
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
        Utils.showToast('Erro de comunicação com servidor', 'danger');
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Export utilities for use in other scripts
window.Utils = Utils;
window.SessionManager = SessionManager;
window.FileHandler = FileHandler;