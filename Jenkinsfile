pipeline {
    agent any
    
    parameters {
        text(name: 'DOWNLOAD_URLS', defaultValue: '', description: 'Comma-separated URLs to download zip files from (leave empty to use local file path)')
        string(name: 'ZIP_FILE_PATH', defaultValue: '', description: 'Path to local zip file (only used if DOWNLOAD_URLS is empty)')
        string(name: 'S3_BUCKET', defaultValue: '', description: 'S3 bucket name for uploading')
        string(name: 'S3_PREFIX', defaultValue: '', description: 'S3 prefix/folder path (optional)')
        choice(name: 'CLOUD_PROVIDER', choices: ['aws', 'aliyun', 'tencent'], description: 'Cloud provider type')
        string(name: 'S3_ENDPOINT', defaultValue: '', description: 'S3 endpoint URL (required for Alibaba Cloud and Tencent Cloud)')
        string(name: 'S3_REGION', defaultValue: 'us-east-1', description: 'S3 region')
        string(name: 'EMAIL_RECIPIENTS', defaultValue: '', description: 'Comma-separated email addresses for notifications')
        string(name: 'SMTP_SERVER', defaultValue: '', description: 'SMTP server address')
        string(name: 'SMTP_PORT', defaultValue: '587', description: 'SMTP server port')
        string(name: 'SMTP_USERNAME', defaultValue: '', description: 'SMTP username')
        password(name: 'SMTP_PASSWORD', defaultValue: '', description: 'SMTP password')
        password(name: 'AWS_ACCESS_KEY_ID', defaultValue: '', description: 'AWS Access Key ID or equivalent')
        password(name: 'AWS_SECRET_ACCESS_KEY', defaultValue: '', description: 'AWS Secret Access Key or equivalent')
    }
    
    environment {
        PYTHON_SCRIPT = 'upload_to_oss.py'
        EXTRACT_DIR = 'extracted_files'
        DOWNLOAD_DIR = 'downloads'
    }
    
    stages {
        stage('Validate Parameters') {
            steps {
                script {
                    echo "Validating required parameters..."
                    
                    // Check that either DOWNLOAD_URLS or ZIP_FILE_PATH is provided
                    if (!params.DOWNLOAD_URLS && !params.ZIP_FILE_PATH) {
                        error("Either DOWNLOAD_URLS or ZIP_FILE_PATH parameter is required")
                    }
                    
                    if (!params.S3_BUCKET) {
                        error("S3_BUCKET parameter is required")
                    }
                    if (!params.EMAIL_RECIPIENTS) {
                        error("EMAIL_RECIPIENTS parameter is required")
                    }
                    if (!params.SMTP_SERVER) {
                        error("SMTP_SERVER parameter is required")
                    }
                    if (!params.SMTP_USERNAME) {
                        error("SMTP_USERNAME parameter is required")
                    }
                    if (!params.SMTP_PASSWORD) {
                        error("SMTP_PASSWORD parameter is required")
                    }
                    if (!params.AWS_ACCESS_KEY_ID || !params.AWS_SECRET_ACCESS_KEY) {
                        error("AWS credentials (ACCESS_KEY_ID and SECRET_ACCESS_KEY) are required")
                    }
                    
                    // Validate endpoint for non-AWS providers
                    if (params.CLOUD_PROVIDER != 'aws' && !params.S3_ENDPOINT) {
                        error("S3_ENDPOINT is required for ${params.CLOUD_PROVIDER} cloud provider")
                    }
                    
                    echo "All required parameters validated successfully"
                }
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    echo "Setting up Python environment..."
                    sh '''
                        python3 --version
                        pip3 install --user -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Process Resources') {
            steps {
                script {
                    if (params.DOWNLOAD_URLS) {
                        echo "Using download URLs mode"
                        echo "URLs: ${params.DOWNLOAD_URLS}"
                        // Resources will be downloaded by Python script
                    } else {
                        echo "Using local file mode"
                        echo "Extracting zip file: ${params.ZIP_FILE_PATH}"
                        sh """
                            mkdir -p ${EXTRACT_DIR}
                            unzip -o "${params.ZIP_FILE_PATH}" -d ${EXTRACT_DIR}
                            echo "Extraction completed successfully"
                            ls -la ${EXTRACT_DIR}
                        """
                    }
                }
            }
        }
        
        stage('Upload to OSS') {
            steps {
                script {
                    echo "Uploading files to ${params.CLOUD_PROVIDER} OSS..."
                    
                    def scriptArgs = ""
                    
                    if (params.DOWNLOAD_URLS) {
                        // Use download URLs mode
                        scriptArgs = """
                            python3 ${PYTHON_SCRIPT} \
                                --download-urls "${params.DOWNLOAD_URLS}" \
                                --download-dir ${DOWNLOAD_DIR} \
                                --extract-dir ${EXTRACT_DIR} \
                                --bucket "${params.S3_BUCKET}" \
                                --prefix "${params.S3_PREFIX}" \
                                --provider "${params.CLOUD_PROVIDER}" \
                                --endpoint "${params.S3_ENDPOINT}" \
                                --region "${params.S3_REGION}" \
                                --access-key "${params.AWS_ACCESS_KEY_ID}" \
                                --secret-key "${params.AWS_SECRET_ACCESS_KEY}" \
                                --email-recipients "${params.EMAIL_RECIPIENTS}" \
                                --smtp-server "${params.SMTP_SERVER}" \
                                --smtp-port "${params.SMTP_PORT}" \
                                --smtp-username "${params.SMTP_USERNAME}" \
                                --smtp-password "${params.SMTP_PASSWORD}"
                        """
                    } else {
                        // Use local source directory mode
                        scriptArgs = """
                            python3 ${PYTHON_SCRIPT} \
                                --source-dir ${EXTRACT_DIR} \
                                --bucket "${params.S3_BUCKET}" \
                                --prefix "${params.S3_PREFIX}" \
                                --provider "${params.CLOUD_PROVIDER}" \
                                --endpoint "${params.S3_ENDPOINT}" \
                                --region "${params.S3_REGION}" \
                                --access-key "${params.AWS_ACCESS_KEY_ID}" \
                                --secret-key "${params.AWS_SECRET_ACCESS_KEY}" \
                                --email-recipients "${params.EMAIL_RECIPIENTS}" \
                                --smtp-server "${params.SMTP_SERVER}" \
                                --smtp-port "${params.SMTP_PORT}" \
                                --smtp-username "${params.SMTP_USERNAME}" \
                                --smtp-password "${params.SMTP_PASSWORD}"
                        """
                    }
                    
                    sh scriptArgs
                }
            }
        }
    }
    
    post {
        success {
            echo 'Pipeline completed successfully!'
            echo "Static resources have been uploaded to ${params.CLOUD_PROVIDER} OSS"
            echo "Deployment notification has been sent to: ${params.EMAIL_RECIPIENTS}"
        }
        failure {
            echo 'Pipeline failed!'
            script {
                // Send failure notification email if SMTP is configured
                if (params.SMTP_SERVER && params.EMAIL_RECIPIENTS) {
                    sh """
                        python3 send_failure_email.py \
                            --smtp-server "${params.SMTP_SERVER}" \
                            --smtp-port "${params.SMTP_PORT}" \
                            --smtp-username "${params.SMTP_USERNAME}" \
                            --smtp-password "${params.SMTP_PASSWORD}" \
                            --recipients "${params.EMAIL_RECIPIENTS}" \
                            --job-name "${env.JOB_NAME}" \
                            --build-number "${env.BUILD_NUMBER}" \
                            --build-url "${env.BUILD_URL}" || true
                    """
                }
            }
        }
        always {
            echo 'Cleaning up temporary files...'
            sh """
                rm -rf ${EXTRACT_DIR}
                rm -rf ${DOWNLOAD_DIR}
                echo 'Cleanup completed'
            """
        }
    }
}
