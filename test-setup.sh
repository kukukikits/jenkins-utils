#!/bin/bash

# Test script for OSS upload functionality
# This script helps you test the upload functionality locally before deploying to Jenkins

set -e

echo "=========================================="
echo "Jenkins OSS Upload - Local Test Script"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3 first: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python 3 is installed: $(python3 --version)"

# Check if pip3 is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip3 is not installed"
    echo "Please install pip3 first"
    exit 1
fi

echo "✓ pip3 is installed"

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install --user -q -r requirements.txt

echo "✓ Dependencies installed"

# Check if boto3 is available
if ! python3 -c "import boto3" 2>/dev/null; then
    echo "❌ Error: boto3 not installed properly"
    echo "Try: pip3 install boto3"
    exit 1
fi

echo "✓ boto3 library is available"
echo ""

# Create test directory
TEST_DIR="/tmp/jenkins-oss-test-$(date +%s)"
mkdir -p "$TEST_DIR"

echo "Creating test files in: $TEST_DIR"
cat > "$TEST_DIR/index.html" <<EOF
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Jenkins OSS Upload Test</h1>
    <p>This is a test page for Jenkins OSS upload functionality.</p>
    <p>Timestamp: $(date)</p>
    <script src="script.js"></script>
</body>
</html>
EOF

cat > "$TEST_DIR/style.css" <<EOF
body {
    font-family: Arial, sans-serif;
    margin: 40px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
}
EOF

cat > "$TEST_DIR/script.js" <<EOF
console.log('Jenkins OSS Upload Test - JavaScript loaded successfully');
document.addEventListener('DOMContentLoaded', function() {
    console.log('Page loaded at:', new Date());
});
EOF

echo "✓ Test files created:"
ls -lh "$TEST_DIR"
echo ""

# Show example command
echo "=========================================="
echo "Test Setup Complete!"
echo "=========================================="
echo ""
echo "To test the upload functionality, run the following command"
echo "(replace the placeholder values with your actual credentials):"
echo ""
echo "python3 upload_to_oss.py \\"
echo "  --source-dir $TEST_DIR \\"
echo "  --bucket YOUR_BUCKET_NAME \\"
echo "  --prefix test/upload-$(date +%Y%m%d-%H%M%S) \\"
echo "  --provider aliyun \\"
echo "  --endpoint https://oss-cn-hangzhou.aliyuncs.com \\"
echo "  --region cn-hangzhou \\"
echo "  --access-key YOUR_ACCESS_KEY \\"
echo "  --secret-key YOUR_SECRET_KEY \\"
echo "  --email-recipients your-email@example.com \\"
echo "  --smtp-server smtp.gmail.com \\"
echo "  --smtp-port 587 \\"
echo "  --smtp-username your-email@gmail.com \\"
echo "  --smtp-password YOUR_APP_PASSWORD"
echo ""
echo "For AWS S3, use:"
echo "  --provider aws"
echo "  --endpoint (leave empty)"
echo "  --region us-east-1"
echo ""
echo "For Tencent Cloud COS, use:"
echo "  --provider tencent"
echo "  --endpoint https://cos.ap-guangzhou.myqcloud.com"
echo "  --region ap-guangzhou"
echo ""
echo "=========================================="
echo "Configuration Examples:"
echo "=========================================="
echo "See config.example.env for detailed configuration examples"
echo "See QUICKSTART.md for step-by-step setup guide"
echo ""
echo "Note: The test directory will be preserved at: $TEST_DIR"
echo "You can delete it manually after testing"
echo ""
