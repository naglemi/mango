#!/bin/bash

# Setup script for grape-reports S3 bucket and testing

echo " Setting up grape-reports bucket..."
echo ""
echo "This script will:"
echo "1. Create the S3 bucket 'grape-reports'"
echo "2. Configure bucket for report storage"
echo "3. Verify SES email setup"
echo ""

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    echo " AWS CLI not installed!"
    echo "Please install: brew install awscli"
    exit 1
fi

# Create S3 bucket
echo "Creating S3 bucket grape-reports..."
aws s3 mb s3://grape-reports --region us-east-1 || echo "Bucket may already exist"

# Create bucket policy for pre-signed URLs to work properly
echo "Setting bucket policy..."
cat > /tmp/bucket-policy.json << 'EOF'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowGetObject",
            "Effect": "Allow",
            "Principal": {
                "AWS": "*"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::grape-reports/*",
            "Condition": {
                "StringLike": {
                    "aws:userId": "AIDAI*"
                }
            }
        }
    ]
}
EOF

# Apply bucket policy (this allows pre-signed URLs to work)
aws s3api put-bucket-policy --bucket grape-reports --policy file:///tmp/bucket-policy.json || true

# Check SES status
echo ""
echo "Checking SES email verification..."
aws ses get-identity-verification-attributes --identities slurmalerts1017@gmail.com --region us-east-1

echo ""
echo " Setup complete!"
echo ""
echo "  IMPORTANT: Make sure slurmalerts1017@gmail.com is verified in AWS SES"
echo "   If not verified, run:"
echo "   aws ses verify-email-identity --email-address slurmalerts1017@gmail.com --region us-east-1"
echo ""
echo "The Report MCP is configured with:"
echo "  Bucket: grape-reports"
echo "  Email: slurmalerts1017@gmail.com"
echo ""
echo "You can now use Report MCP in Claude Code!"