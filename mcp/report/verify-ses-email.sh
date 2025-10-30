#!/bin/bash

# SES Email Verification Script

EMAIL="slurmalerts1017@gmail.com"
REGION="us-east-1"

echo " AWS SES Email Verification"
echo "============================"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo " AWS CLI not installed!"
    echo ""
    echo "Please install it first:"
    echo "1. The installer should be open (AWSCLIV2.pkg)"
    echo "2. Or run: brew install awscli"
    exit 1
fi

# Send verification email
echo " Sending verification email to $EMAIL..."
aws ses verify-email-identity --email-address "$EMAIL" --region "$REGION"

if [ $? -eq 0 ]; then
    echo " Verification email sent!"
    echo ""
    echo "  IMPORTANT: Check your email at $EMAIL"
    echo "   Look for an email from AWS with subject:"
    echo "   'Amazon Web Services – Email Address Verification Request'"
    echo ""
    echo "   Click the verification link in that email!"
    echo ""
    
    # Check current status
    echo "Checking current verification status..."
    aws ses get-identity-verification-attributes --identities "$EMAIL" --region "$REGION" --output table
    
    echo ""
    echo "After clicking the link, run this script again to check status."
else
    echo " Failed to send verification email"
    echo "Check your AWS credentials are configured correctly"
fi