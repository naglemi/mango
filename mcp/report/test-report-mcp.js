#!/usr/bin/env node

// Test script to simulate Report MCP functionality
import { S3Client, PutObjectCommand, GetObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { SESClient, SendEmailCommand } from '@aws-sdk/client-ses';
import { readFileSync } from 'fs';

const config = {
  bucketName: 'grape-reports',
  region: 'us-east-1',
  emailFrom: 'slurmalerts1017@gmail.com',
  emailTo: 'slurmalerts1017@gmail.com',
};

const s3Client = new S3Client({ region: config.region });
const sesClient = new SESClient({ region: config.region });

async function sendTestReport() {
  const agentName = 'TestAgent';
  const title = 'The Three Cats of Maple Street';
  const timestamp = new Date().toISOString();
  
  // Read the cat story
  const storyContent = `The Three Mischievous Cats of Maple Street

On a quiet suburban street lined with maple trees, three cats ruled their respective domains with paws of iron and hearts of mischief.

First, there was Whiskers, an orange tabby who considered himself the intellectual of the group. He spent his mornings perched on the Henderson's porch, studying the patterns of mail delivery and plotting the optimal moment to dart between the mailman's legs.

Next door lived Midnight, a sleek black cat with eyes like emeralds. She was the acrobat of the trio, famous for her death-defying leaps from fence to fence and her uncanny ability to appear on rooftops without anyone seeing her climb.

At the end of the street resided Sir Fluffington III (though everyone just called him "Fluffy"), a majestic Persian whose fur was so voluminous that he appeared to be twice his actual size.

The three would meet every evening at sunset to share their adventures and plot new schemes...`;

  const date = new Date();
  const dateStr = date.toISOString().split('T')[0];
  const timeStr = date.toTimeString().split(' ')[0].replace(/:/g, '-');
  const reportFolder = `${agentName}/${dateStr}_${timeStr}`;

  console.log(' Uploading cat story report...');
  
  // Use real cat images
  const images = [
    { name: 'whiskers_orange_tabby.jpg', path: '/tmp/cat_images/whiskers_orange_tabby.jpg' },
    { name: 'midnight_black_cat.jpg', path: '/tmp/cat_images/midnight_black_cat.jpg' },
    { name: 'fluffington_persian.jpg', path: '/tmp/cat_images/fluffington_persian.jpg' }
  ];
  
  // Upload real images
  const imageUrls = [];
  for (const img of images) {
    const key = `${reportFolder}/${img.name}`;
    const imageData = readFileSync(img.path);
    await s3Client.send(new PutObjectCommand({
      Bucket: config.bucketName,
      Key: key,
      Body: imageData,
      ContentType: 'image/jpeg',
    }));
    
    const url = await getSignedUrl(s3Client, new GetObjectCommand({
      Bucket: config.bucketName,
      Key: key,
    }), { expiresIn: 604800 });
    
    imageUrls.push({ filename: img.name, url });
    console.log(` Uploaded ${img.name}`);
  }
  
  // Create HTML index
  const indexHtml = `<!DOCTYPE html>
<html>
<head>
  <title>${title}</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
    .content { background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0; }
    .files { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
    .file { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: white; }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <p><strong>From:</strong> ${agentName} | <strong>Time:</strong> ${timestamp}</p>
  
  <div class="content">
    <h2>Story</h2>
    <pre>${storyContent}</pre>
  </div>
  
  <h2>Cat Pictures (3)</h2>
  <div class="files">
    ${imageUrls.map(img => `
    <div class="file">
      <strong>${img.filename}</strong><br>
      <a href="${img.url}" target="_blank">View Image</a>
      <img src="${img.url}" style="max-width:100%; margin-top:10px;" alt="${img.filename}">
    </div>`).join('')}
  </div>
</body>
</html>`;
  
  // Upload index
  const indexKey = `${reportFolder}/index.html`;
  await s3Client.send(new PutObjectCommand({
    Bucket: config.bucketName,
    Key: indexKey,
    Body: indexHtml,
    ContentType: 'text/html',
  }));
  
  const indexUrl = await getSignedUrl(s3Client, new GetObjectCommand({
    Bucket: config.bucketName,
    Key: indexKey,
  }), { expiresIn: 604800 });
  
  console.log(' Created report index page');
  
  // Send email
  const emailParams = {
    Source: config.emailFrom,
    Destination: { ToAddresses: [config.emailTo] },
    Message: {
      Subject: { Data: `[${agentName}] ${title} - ${timestamp}` },
      Body: {
        Html: {
          Data: `
<h2>Cat Story Report</h2>
<p>${storyContent.substring(0, 200)}...</p>
<p><a href="${indexUrl}" style="background:#0066cc; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">View Full Report with 3 Cat Pictures</a></p>
`
        }
      }
    }
  };
  
  try {
    await sesClient.send(new SendEmailCommand(emailParams));
    console.log(' Email sent successfully!');
  } catch (error) {
    console.error(' Email failed:', error.message);
    console.log('Make sure slurmalerts1017@gmail.com is verified in SES');
  }
  
  console.log('\n Report Summary:');
  console.log(`Subject: [${agentName}] ${title}`);
  console.log(`Report URL: ${indexUrl}`);
  console.log(`Files: ${images.length} cat pictures`);
}

sendTestReport().catch(console.error);