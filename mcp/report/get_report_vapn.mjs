#!/usr/bin/env node

// Retrieve report VAPN from S3 using report MCP credentials

import { S3Client, GetObjectCommand, ListObjectsV2Command } from '@aws-sdk/client-s3';

// Hardcoded credentials for usability-reports bucket
const AWS_CREDENTIALS = {
  accessKeyId: 'AKIATQPD7I25OJYV77MB',
  secretAccessKey: '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',
};

const s3Client = new S3Client({
  region: 'us-east-1',
  credentials: AWS_CREDENTIALS
});

async function getReportByTag(tag) {
  console.log(`Searching for report with tag: ${tag}`);

  // List all objects in the bucket
  const listCommand = new ListObjectsV2Command({
    Bucket: 'usability-reports',
    Prefix: 'Detective Righteous/',
  });

  const response = await s3Client.send(listCommand);

  if (!response.Contents) {
    console.log('No objects found');
    return;
  }

  // Filter for metadata.json files
  const metadataFiles = response.Contents
    .filter(obj => obj.Key.endsWith('metadata.json'))
    .sort((a, b) => new Date(b.LastModified) - new Date(a.LastModified));

  console.log(`Found ${metadataFiles.length} metadata files`);

  // Search for matching report
  for (const metaFile of metadataFiles) {
    try {
      const getMetaCommand = new GetObjectCommand({
        Bucket: 'usability-reports',
        Key: metaFile.Key,
      });

      const metaResponse = await s3Client.send(getMetaCommand);
      const metaContent = await metaResponse.Body.transformToString();
      const metadata = JSON.parse(metaContent);

      if (metadata.tag === tag.toUpperCase()) {
        console.log(`\nFound report ${tag}:`);
        console.log(`Agent: ${metadata.agentName}`);
        console.log(`Title: ${metadata.title}`);
        console.log(`Time: ${metadata.timestamp}`);
        console.log(`Index Key: ${metadata.indexKey}`);

        // Get the actual report HTML
        const getReportCommand = new GetObjectCommand({
          Bucket: 'usability-reports',
          Key: metadata.indexKey,
        });

        const reportResponse = await s3Client.send(getReportCommand);
        const reportHtml = await reportResponse.Body.transformToString();

        // Extract the markdown content from HTML
        // The content is in the div with class "content"
        const contentMatch = reportHtml.match(/<div class="content">[\s\S]*?<h2>Report Content<\/h2>([\s\S]*?)<\/div>/);

        if (contentMatch) {
          console.log('\n' + '='.repeat(80));
          console.log('REPORT CONTENT:');
          console.log('='.repeat(80));

          // Remove HTML tags to get plain text
          let content = contentMatch[1];
          content = content.replace(/<[^>]*>/g, '');
          content = content.replace(/&lt;/g, '<');
          content = content.replace(/&gt;/g, '>');
          content = content.replace(/&amp;/g, '&');
          content = content.trim();

          console.log(content);
          console.log('\n' + '='.repeat(80));
        }

        return;
      }
    } catch (error) {
      console.error(`Error reading ${metaFile.Key}:`, error.message);
    }
  }

  console.log(`No report found with tag ${tag}`);
}

// Run
getReportByTag('VAPN').catch(error => {
  console.error('Error:', error);
  process.exit(1);
});
