#!/usr/bin/env node

import { S3Client, CreateBucketCommand, PutBucketPolicyCommand } from '@aws-sdk/client-s3';

const s3Client = new S3Client({ region: 'us-east-1' });

async function createBucket() {
  try {
    // Create bucket
    await s3Client.send(new CreateBucketCommand({
      Bucket: 'grape-reports',
      // For us-east-1, we don't specify LocationConstraint
    }));
    console.log(' Created bucket: grape-reports');
  } catch (error) {
    if (error.name === 'BucketAlreadyExists' || error.name === 'BucketAlreadyOwnedByYou') {
      console.log(' Bucket already exists: grape-reports');
    } else {
      throw error;
    }
  }
  
  // Set bucket policy for pre-signed URLs
  const policy = {
    Version: '2012-10-17',
    Statement: [
      {
        Sid: 'AllowPublicRead',
        Effect: 'Allow',
        Principal: '*',
        Action: 's3:GetObject',
        Resource: 'arn:aws:s3:::grape-reports/*',
        Condition: {
          StringLike: {
            's3:signatureversion': 'AWS4-HMAC-SHA256'
          }
        }
      }
    ]
  };
  
  try {
    await s3Client.send(new PutBucketPolicyCommand({
      Bucket: 'grape-reports',
      Policy: JSON.stringify(policy)
    }));
    console.log(' Set bucket policy');
  } catch (error) {
    console.log('  Could not set bucket policy:', error.message);
  }
}

createBucket().catch(console.error);