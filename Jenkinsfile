pipeline {
// Change agent from 'docker' to 'any' to run directly on the executor machine
agent any

// Set environment variables for the script if needed (optional)
environment {
// Define the path to the virtual environment for easy reference
VENV_DIR = 'venv'
PYTHON_BIN = 'venv/bin/python3'
ANALYTICS_LEVEL = 'CRITICAL'
// Define a simulated deployment directory
PROD_DEPLOY_DIR = 'production_release'

// NEW: Create a versioned filename using the Jenkins BUILD_NUMBER
// The BUILD_NUMBER is automatically injected into the 'env' map by Jenkins.
VERSIONED_FILENAME = "data_processor_v${env.BUILD_NUMBER}.py"
}

stages {
stage('Checkout Code') {
steps {
echo 'Source code assumed checked out by Jenkins SCM.'
}
}

stage('Setup Environment') {
steps {
echo "Creating virtual environment and installing dependencies..."
// 1. Create the virtual environment using python3
sh "python3 -m venv ${env.VENV_DIR}"

// 2. Install dependencies using the Python binary inside the venv
sh "${env.PYTHON_BIN} -m pip install -r requirements.txt"

}

}

stage('Run Unit Tests') {
steps {
echo "Running unit tests using pytest from virtual environment..."
// 3. Execute pytest using the Python binary inside the venv
sh "${env.PYTHON_BIN} -m pytest"
}
}

stage('Run Data Analysis') {
steps {
sh """
echo "Starting production data analysis script..."

Execute the main script using the Python binary inside the venv

${env.PYTHON_BIN} data_processor.py
"""
}
}

// --- CD STAGE: Now performs a simulated file deployment with versioning ---
stage('Success & Deployment') {
// This stage will now run automatically because the previous stages succeeded.
steps {
echo 'Compliance check PASSED. Analysis successful: All dataset memory usage is compliant with the threshold.'

// 5. Create a simulated production directory
sh "mkdir -p ${env.PROD_DEPLOY_DIR}"

// 6. ACTUAL DEPLOYMENT: Copy the artifact using the VERSIONED_FILENAME
sh "cp data_processor.py ${env.PROD_DEPLOY_DIR}/${env.VERSIONED_FILENAME}"

// 7. Verification Step - List the contents of the deployment folder
echo 'VERIFICATION: Listing files in simulated production environment...'
sh "ls -l ${env.PROD_DEPLOY_DIR}/"

// FIX: Changed quoting from double quotes to single quotes to prevent Groovy parsing error.
sh "echo 'CD SUCCESS: Deployed version ${env.BUILD_NUMBER} to simulated path: ${env.PROD_DEPLOY_DIR}/${env.VERSIONED_FILENAME}'"
}

}
// --- END CD STAGE ---

} // End of stages block

post {
// Define actions that run after the entire pipeline finishes
always {
// Archive the generated report file as a build artifact regardless of build status
archiveArtifacts artifacts: 'analysis_report.md', onlyIfSuccessful: false

// Clean up the generated database, report file, virtual environment, and simulated production folder
sh 'rm -f object_store.db'
sh 'rm -f analysis_report.md'
sh "rm -rf ${env.VENV_DIR}" // Clean up the venv directory
sh "rm -rf ${env.PROD_DEPLOY_DIR}" // Clean up the simulated deploy directory
echo 'Cleanup complete.'

}
failure {
echo 'One or more stages failed (Tests or Data Analysis). The full report is archived as an artifact.'
}

} // End of post block
} // FINAL CLOSING BRACE FOR THE PIPELINE BLOCK
