// Processing monitoring for MVP RPA Documentation

$(document).ready(function() {
    // Processing monitor class
    class ProcessingMonitor {
        constructor(sessionId) {
            this.sessionId = sessionId;
            this.pollInterval = null;
            this.currentStep = 0;
            this.steps = [
                { id: 'step-upload', name: 'Upload', threshold: 10 },
                { id: 'step-transcription', name: 'Transcrição', threshold: 30 },
                { id: 'step-ocr', name: 'OCR', threshold: 50 },
                { id: 'step-correlation', name: 'Correlação', threshold: 70 },
                { id: 'step-ai', name: 'IA', threshold: 90 },
                { id: 'step-complete', name: 'Completo', threshold: 100 }
            ];
        }

        start() {
            this.pollInterval = setInterval(() => {
                this.checkStatus();
            }, 2000);
        }

        stop() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
                this.pollInterval = null;
            }
        }

        async checkStatus() {
            try {
                const response = await fetch(`/status/${this.sessionId}`);
                const data = await response.json();
                
                this.handleStatusUpdate(data);
            } catch (error) {
                console.error('Error checking status:', error);
                this.handleError('Erro de comunicação');
            }
        }

        handleStatusUpdate(data) {
            const status = data.status;
            
            switch (status) {
                case 'uploading':
                    this.updateProgress(10, 'Arquivos enviados');
                    break;
                case 'processing':
                    this.simulateProcessingProgress();
                    break;
                case 'completed':
                    this.updateProgress(100, 'Processamento concluído!');
                    this.onComplete(data);
                    break;
                case 'error':
                    this.handleError('Erro no processamento');
                    break;
            }
        }

        simulateProcessingProgress() {
            // Simula progresso durante processamento
            const currentProgress = parseInt($('#progressBar').css('width')) || 20;
            
            if (currentProgress < 90) {
                const newProgress = Math.min(currentProgress + Math.random() * 10, 90);
                const currentStepIndex = this.steps.findIndex(step => newProgress < step.threshold);
                const currentStepName = currentStepIndex > 0 ? this.steps[currentStepIndex - 1].name : 'Processando';
                
                this.updateProgress(newProgress, `Processando ${currentStepName.toLowerCase()}...`);
            }
        }

        updateProgress(percent, text) {
            const progressBar = $('#progressBar');
            const statusText = $('#statusText');

            progressBar.css('width', percent + '%');
            progressBar.text(Math.round(percent) + '%');
            statusText.text(text);

            this.updateStepIndicators(percent);
        }

        updateStepIndicators(percent) {
            this.steps.forEach((step, index) => {
                const element = $(`#${step.id}`);
                const icon = element.find('i');

                if (percent >= step.threshold) {
                    // Step completed
                    element.removeClass('current').addClass('completed');
                    icon.removeClass('fa-circle fa-circle-notch fa-spin text-primary text-muted')
                        .addClass('fa-check-circle text-success');
                } else if (percent >= step.threshold - 20) {
                    // Step in progress
                    element.removeClass('completed').addClass('current');
                    icon.removeClass('fa-circle fa-check-circle text-success text-muted')
                        .addClass('fa-circle-notch fa-spin text-primary');
                } else {
                    // Step pending
                    element.removeClass('current completed');
                    icon.removeClass('fa-circle-notch fa-spin fa-check-circle text-primary text-success')
                        .addClass('fa-circle text-muted');
                }
            });
        }

        onComplete(data) {
            this.stop();
            
            // Update final progress
            this.updateProgress(100, 'Documentação gerada com sucesso!');
            
            // Show result section
            setTimeout(() => {
                $('#progressSection').slideUp();
                $('#resultSection').slideDown();
                
                // Update session info
                if (data.session_id) {
                    $('#sessionId').text(data.session_id.substring(0, 8));
                }
                
                // Setup buttons
                this.setupResultButtons(data.session_id);
                
                // Show success toast
                Utils.showToast('Processamento concluído com sucesso!', 'success');
            }, 1000);
        }

        setupResultButtons(sessionId) {
            $('#reviewBtn').off('click').on('click', function() {
                window.location.href = `/review/${sessionId}`;
            });

            $('#downloadBtn').off('click').on('click', function() {
                // Start download
                const link = document.createElement('a');
                link.href = `/export/${sessionId}/docx`;
                link.download = `documentacao_rpa_${sessionId.substring(0, 8)}.docx`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            });
        }

        handleError(message) {
            this.stop();
            
            // Update progress bar to error state
            const progressBar = $('#progressBar');
            progressBar.removeClass('progress-bar-striped progress-bar-animated')
                      .addClass('bg-danger');
            progressBar.css('width', '100%');
            $('#statusText').text(message);
            
            // Mark current step as error
            const currentStepElement = $('.step.current');
            if (currentStepElement.length > 0) {
                const icon = currentStepElement.find('i');
                icon.removeClass('fa-circle-notch fa-spin text-primary')
                    .addClass('fa-exclamation-circle text-danger');
            }
            
            // Show error toast
            Utils.showToast(message, 'danger');
            
            // Show retry option
            setTimeout(() => {
                $('#progressSection .card-body').append(`
                    <div class="text-center mt-3">
                        <button class="btn btn-outline-primary" onclick="location.reload()">
                            <i class="fas fa-redo me-2"></i>
                            Tentar Novamente
                        </button>
                    </div>
                `);
            }, 2000);
        }
    }

    // Export for global use
    window.ProcessingMonitor = ProcessingMonitor;
});

// Processing utilities
const ProcessingUtils = {
    // Estimate processing time based on file sizes
    estimateProcessingTime: function(transcriptionSize, screenshotCount) {
        let estimatedTime = 30; // Base time in seconds
        
        // Add time based on transcription size
        estimatedTime += Math.ceil(transcriptionSize / (1024 * 1024)) * 10; // 10s per MB
        
        // Add time based on screenshot count
        estimatedTime += screenshotCount * 5; // 5s per screenshot
        
        return Math.min(estimatedTime, 300); // Max 5 minutes
    },

    // Format estimated time
    formatEstimatedTime: function(seconds) {
        if (seconds < 60) {
            return `~${seconds} segundos`;
        } else {
            const minutes = Math.ceil(seconds / 60);
            return `~${minutes} minuto${minutes > 1 ? 's' : ''}`;
        }
    },

    // Show processing estimate
    showProcessingEstimate: function(transcriptionSize, screenshotCount) {
        const estimatedTime = this.estimateProcessingTime(transcriptionSize, screenshotCount);
        const formattedTime = this.formatEstimatedTime(estimatedTime);
        
        const estimateHtml = `
            <div class="alert alert-info mt-3" id="processingEstimate">
                <i class="fas fa-clock me-2"></i>
                <strong>Tempo estimado:</strong> ${formattedTime}
                <br>
                <small class="text-muted">
                    Baseado em ${Math.ceil(transcriptionSize / 1024)} KB de transcrição e ${screenshotCount} screenshot${screenshotCount !== 1 ? 's' : ''}
                </small>
            </div>
        `;
        
        $('#progressSection .card-body').prepend(estimateHtml);
        
        // Remove estimate after processing starts
        setTimeout(() => {
            $('#processingEstimate').fadeOut();
        }, 3000);
    }
};

// Export utilities
window.ProcessingUtils = ProcessingUtils;