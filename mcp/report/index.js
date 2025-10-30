#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { 
  CallToolRequestSchema, 
  ListToolsRequestSchema 
} from '@modelcontextprotocol/sdk/types.js';
import { 
  S3Client, 
  PutObjectCommand, 
  ListObjectsV2Command,
  GetObjectCommand 
} from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';
import { SESClient, SendEmailCommand, SendRawEmailCommand } from '@aws-sdk/client-ses';
import { lookup } from 'mime-types';
import { readFileSync, writeFileSync, unlinkSync, statSync, mkdirSync, existsSync, appendFileSync } from 'fs';
import { basename, join } from 'path';
import { execSync } from 'child_process';
import MarkdownIt from 'markdown-it';
import fetch from 'node-fetch';

// Initialize markdown parser
const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true
});

// Configuration from environment
const config = {
  bucketName: process.env.REPORT_BUCKET || 'mango-reports',
  region: process.env.AWS_REGION || 'us-east-1',
  emailFrom: process.env.REPORT_EMAIL_FROM || 'reports@example.com',
  emailTo: process.env.REPORT_EMAIL_TO || 'user@example.com',
  urlExpiration: parseInt(process.env.REPORT_URL_EXPIRATION || '604800'), // 7 days default
  localFolder: process.env.USABILIDE_REPORT_FOLDER || null,
};

// Check if local mode is enabled
// Local mode is enabled if USABILIDE_REPORT_FOLDER is set to a path (not "EMAIL", not empty)
function isLocalMode() {
  return config.localFolder &&
         config.localFolder !== 'EMAIL' &&
         config.localFolder.trim() !== '';
}

// AWS CREDENTIALS for Report MCP (S3/SES mode only)
// In EMAIL mode (cloud), these MUST be set via environment variables:
//   REPORT_AWS_ACCESS_KEY_ID
//   REPORT_AWS_SECRET_ACCESS_KEY
//
// These are DIFFERENT credentials from CLAUDE.md!
// - CLAUDE.md credentials: For general EC2/AWS operations (account 746491138304)
// - Report MCP credentials: For mango-reports S3 bucket and SES (different account)
//
// Set these in ~/.bashrc or via setup script for EMAIL mode
// LOCAL mode (USABILIDE_REPORT_FOLDER set to path) does not need AWS credentials

// Only configure AWS clients if in EMAIL mode (not LOCAL mode)
let s3Client, sesClient;

if (!isLocalMode()) {
  // EMAIL mode - require AWS credentials from environment
  const reportAwsAccessKey = process.env.REPORT_AWS_ACCESS_KEY_ID;
  const reportAwsSecretKey = process.env.REPORT_AWS_SECRET_ACCESS_KEY;

  if (!reportAwsAccessKey || !reportAwsSecretKey) {
    console.error('ERROR: Report MCP in EMAIL mode requires AWS credentials');
    console.error('Please set environment variables:');
    console.error('  REPORT_AWS_ACCESS_KEY_ID');
    console.error('  REPORT_AWS_SECRET_ACCESS_KEY');
    console.error('');
    console.error('These should be configured during setup via setup-workflows.sh');
    console.error('Or add to ~/.bashrc:');
    console.error('  export REPORT_AWS_ACCESS_KEY_ID="your-key-here"');
    console.error('  export REPORT_AWS_SECRET_ACCESS_KEY="your-secret-here"');
    process.exit(1);
  }

  const AWS_CREDENTIALS = {
    accessKeyId: reportAwsAccessKey,
    secretAccessKey: reportAwsSecretKey,
  };

  // Initialize AWS clients with explicit credentials
  s3Client = new S3Client({
    region: config.region,
    credentials: AWS_CREDENTIALS
  });
  sesClient = new SESClient({
    region: config.region,
    credentials: AWS_CREDENTIALS
  });
}

// Helper to generate random 4-character alphanumeric tag
function generateReportTag() {
  const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  let tag = '';
  for (let i = 0; i < 4; i++) {
    tag += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return tag;
}

// Helper to generate S3 key
function generateS3Key(agentName, filename) {
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0];
  const timeStr = date.toTimeString().split(' ')[0].replace(/:/g, '-');
  return `${agentName}/${dateStr}_${timeStr}/${filename}`;
}

// Helper to upload file to S3
async function uploadToS3(key, content, contentType) {
  const command = new PutObjectCommand({
    Bucket: config.bucketName,
    Key: key,
    Body: content,
    ContentType: contentType,
  });

  await s3Client.send(command);

  // Generate pre-signed URL
  const getCommand = new GetObjectCommand({
    Bucket: config.bucketName,
    Key: key,
  });

  const url = await getSignedUrl(s3Client, getCommand, {
    expiresIn: config.urlExpiration
  });

  return url;
}

// Helper to save file locally
function saveToLocal(relativePath, content) {
  const fullPath = join(config.localFolder, relativePath);
  const dir = fullPath.substring(0, fullPath.lastIndexOf('/'));

  // Create directory structure
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  // Write file
  writeFileSync(fullPath, content);

  // Return local file:// URL
  return `file://${fullPath}`;
}

// Helper to create local report folder structure
// Format: {localFolder}/{agentName}/{YYYY-MM-DD}_{TAG}/
function createLocalReportFolder(agentName, reportTag) {
  const date = new Date();
  const dateStr = date.toISOString().split('T')[0];
  const folderName = `${dateStr}_${reportTag}`;
  const reportPath = join(agentName, folderName);

  return reportPath;
}

// Helper to create HTML index for local reports
function createLocalReportIndex(agentName, title, textContent, files, timestamp, reportTag) {
  const date = new Date(timestamp);
  const timeOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    timeZone: 'America/New_York',
    timeZoneName: 'short'
  };
  const formattedTime12h = date.toLocaleString('en-US', timeOptions);

  const time24Options = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'America/New_York',
    timeZoneName: 'short'
  };
  const formattedTime24h = date.toLocaleString('en-US', time24Options);

  const html = `<!DOCTYPE html>
<html>
<head>
  <title>${agentName} - ${title}</title>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }
    h1, h2, h3 { color: #333; }
    .metadata { color: #666; margin-bottom: 20px; padding: 10px; background: #f9f9f9; border-radius: 5px; }
    .metadata .tag { font-size: 1.2em; font-weight: bold; color: #0066cc; background: #e3f2fd; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 10px; }
    .metadata .local-mode { color: #ff6600; font-weight: bold; background: #fff3e0; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 10px; }
    .content { background: #fff; padding: 30px; border-radius: 5px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .content h2:first-child { margin-top: 0; }
    pre { white-space: pre-wrap; word-wrap: break-word; background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
    code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #f5f5f5; font-weight: bold; }
    blockquote { border-left: 4px solid #ddd; margin: 1em 0; padding-left: 1em; color: #666; }
    .files { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
    .file { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: white; }
    .file img { max-width: 100%; height: auto; margin-top: 10px; }
    .file a { color: #0066cc; text-decoration: none; }
    .file a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <div class="metadata">
    <div class="tag">Report Tag: ${reportTag}</div>
    <div class="local-mode"> LOCAL MODE</div>
    <strong>Agent:</strong> ${agentName}<br>
    <strong>Time (12-hour):</strong> ${formattedTime12h}<br>
    <strong>Time (24-hour):</strong> ${formattedTime24h}
  </div>

  <div class="content">
    <h2>Report Content</h2>
    ${renderMarkdownForMathJax(textContent)}
  </div>

  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true,
        processEnvironments: true,
        processRefs: true,
        packages: {'[+]': ['ams', 'noerrors']}
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
        processHtmlClass: 'tex2jax_process|content',
        ignoreHtmlClass: 'tex2jax_ignore',
        renderActions: {
          findScript: [10, function (doc) {
            for (const node of document.querySelectorAll('script[type^="math/tex"]')) {
              const display = !!node.type.match(/; *mode=display/);
              const math = new doc.options.MathItem(node.textContent, doc.inputJax[0], display);
              const text = document.createTextNode('');
              node.parentNode.replaceChild(text, node);
              math.start = {node: text, delim: '', n: 0};
              math.end = {node: text, delim: '', n: 0};
              doc.math.push(math);
            }
          }, '']
        }
      },
      startup: {
        pageReady: () => {
          return MathJax.startup.defaultPageReady().then(() => {
            console.log('MathJax initial typesetting complete');
          });
        }
      },
      loader: {
        load: ['[tex]/ams', '[tex]/noerrors']
      }
    };
  </script>
  <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>

  ${files.length > 0 ? `
  <h2>Attachments (${files.length})</h2>
  <div class="files">
    ${files.map(file => `
    <div class="file">
      <strong>${file.filename}</strong><br>
      <a href="${file.filename}" target="_blank">Open</a>
      ${file.filename.match(/\.(png|jpg|jpeg|gif|webp)$/i) ?
        `<br><img src="${file.filename}" alt="${file.filename}">` : ''}
    </div>
    `).join('')}
  </div>
  ` : ''}
</body>
</html>`;

  return html;
}

// Helper to render markdown while preserving LaTeX for MathJax
function renderMarkdownForMathJax(markdown) {
  // Store LaTeX expressions temporarily
  const mathBlocks = [];
  let counter = 0;
  
  // Replace display math first
  let preserved = markdown.replace(/\$\$([^$]+)\$\$/g, (match, math) => {
    const placeholder = `MATHBLOCK${counter}`;
    mathBlocks[counter] = `$$${math}$$`;
    counter++;
    return placeholder;
  });
  
  // Replace inline math
  preserved = preserved.replace(/\$([^$\n]+)\$/g, (match, math) => {
    const placeholder = `MATHBLOCK${counter}`;
    mathBlocks[counter] = `$${math}$`;
    counter++;
    return placeholder;
  });
  
  // Render markdown to HTML
  let html = md.render(preserved);
  
  // Restore math expressions
  for (let i = 0; i < counter; i++) {
    html = html.replace(`MATHBLOCK${i}`, mathBlocks[i]);
  }
  
  return html;
}

// Helper to create HTML index page for a report
function createReportIndex(agentName, title, textContent, files, timestamp, reportTag) {
  const date = new Date(timestamp);
  const timeOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
    timeZone: 'America/New_York',
    timeZoneName: 'short'
  };
  const formattedTime12h = date.toLocaleString('en-US', timeOptions);
  
  // For 24-hour format in Eastern Time
  const time24Options = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: 'America/New_York',
    timeZoneName: 'short'
  };
  const formattedTime24h = date.toLocaleString('en-US', time24Options);
  
  const html = `<!DOCTYPE html>
<html>
<head>
  <title>${agentName} - ${title}</title>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; line-height: 1.6; }
    h1, h2, h3 { color: #333; }
    .metadata { color: #666; margin-bottom: 20px; padding: 10px; background: #f9f9f9; border-radius: 5px; }
    .metadata .tag { font-size: 1.2em; font-weight: bold; color: #0066cc; background: #e3f2fd; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 10px; }
    .content { background: #fff; padding: 30px; border-radius: 5px; margin-bottom: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .content h2:first-child { margin-top: 0; }
    pre { white-space: pre-wrap; word-wrap: break-word; background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
    code { background: #f5f5f5; padding: 2px 4px; border-radius: 3px; font-family: monospace; }
    table { border-collapse: collapse; width: 100%; margin: 15px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background: #f5f5f5; font-weight: bold; }
    blockquote { border-left: 4px solid #ddd; margin: 1em 0; padding-left: 1em; color: #666; }
    .files { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
    .file { border: 1px solid #ddd; padding: 15px; border-radius: 5px; background: white; }
    .file img { max-width: 100%; height: auto; margin-top: 10px; }
    .file a { color: #0066cc; text-decoration: none; }
    .file a:hover { text-decoration: underline; }
    /* MathJax styling */
    .MathJax { font-size: 1.1em; }
    mjx-container { margin: 0.5em 0; }
    mjx-container[display="true"] { margin: 1em 0; }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <div class="metadata">
    <div class="tag">Report Tag: ${reportTag}</div>
    <strong>Agent:</strong> ${agentName}<br>
    <strong>Time (12-hour):</strong> ${formattedTime12h}<br>
    <strong>Time (24-hour):</strong> ${formattedTime24h}
  </div>
  
  <div class="content">
    <h2>Report Content</h2>
    ${renderMarkdownForMathJax(textContent)}
  </div>
  
  <script>
    window.MathJax = {
      tex: {
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
        processEscapes: true,
        processEnvironments: true,
        processRefs: true,
        packages: {'[+]': ['ams', 'noerrors']}
      },
      options: {
        skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
        processHtmlClass: 'tex2jax_process|content',
        ignoreHtmlClass: 'tex2jax_ignore',
        renderActions: {
          findScript: [10, function (doc) {
            for (const node of document.querySelectorAll('script[type^="math/tex"]')) {
              const display = !!node.type.match(/; *mode=display/);
              const math = new doc.options.MathItem(node.textContent, doc.inputJax[0], display);
              const text = document.createTextNode('');
              node.parentNode.replaceChild(text, node);
              math.start = {node: text, delim: '', n: 0};
              math.end = {node: text, delim: '', n: 0};
              doc.math.push(math);
            }
          }, '']
        }
      },
      startup: {
        pageReady: () => {
          return MathJax.startup.defaultPageReady().then(() => {
            console.log('MathJax initial typesetting complete');
            // Log any math elements found
            const mathElements = document.querySelectorAll('mjx-container');
            console.log('Found ' + mathElements.length + ' math elements');
          });
        }
      },
      loader: {
        load: ['[tex]/ams', '[tex]/noerrors']
      }
    };
  </script>
  <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
  <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
  
  ${files.length > 0 ? `
  <h2>Attachments (${files.length})</h2>
  <div class="files">
    ${files.map(file => `
    <div class="file">
      <strong>${file.filename}</strong><br>
      <a href="${file.url}" target="_blank">View/Download</a>
      ${file.filename.match(/\.(png|jpg|jpeg|gif|webp)$/i) ? 
        `<br><img src="${file.url}" alt="${file.filename}">` : ''}
    </div>
    `).join('')}
  </div>
  ` : ''}
</body>
</html>`;
  
  return html;
}

// Helper to check if file is an image
function isImage(filename) {
  return /\.(png|jpg|jpeg|gif|webp)$/i.test(filename);
}


// Helper to convert LaTeX to image URL using online service
async function latexToImageUrl(latex, isDisplay = false) {
  try {
    // Use codecogs API for LaTeX rendering - PNG format for email compatibility
    const fontSize = isDisplay ? '18' : '14';
    const dpi = '150';
    const backgroundColor = 'white';
    const foregroundColor = 'black';
    
    // URL encode the LaTeX
    const encodedLatex = encodeURIComponent(latex);
    
    // Generate PNG image URL (better email support than SVG)
    const imageUrl = `https://latex.codecogs.com/png.image?\\dpi{${dpi}}\\bg{${backgroundColor}}\\large{${encodedLatex}}`;
    
    return imageUrl;
  } catch (error) {
    console.error('LaTeX to image conversion failed:', error);
    return null;
  }
}


// Helper to render markdown with LaTeX images for email
async function convertMarkdownToEmailHtmlWithImages(markdown, agentName, reportFolder) {
  // Store LaTeX expressions and their replacements
  const mathReplacements = [];
  let counter = 0;
  
  // First pass: extract and replace math blocks
  let processedText = markdown;
  
  // Replace display math
  const displayMatches = [...markdown.matchAll(/\$\$([^$]+)\$\$/g)];
  for (const match of displayMatches) {
    const placeholder = `MATHIMG${counter}`;
    // Get image URL from codecogs
    const imageUrl = await latexToImageUrl(match[1], true);
    
    if (imageUrl) {
      try {
        // Fetch the image
        const response = await fetch(imageUrl);
        if (response.ok) {
          const buffer = await response.buffer();
          
          // Upload to S3
          const filename = `math_${counter}.png`;
          const s3Key = `${reportFolder}/${filename}`;
          const s3Url = await uploadToS3(s3Key, buffer, 'image/png');
          
          mathReplacements[counter] = `<div style="text-align: center; margin: 15px 0;">
            <img src="${s3Url}" alt="${match[1]}" style="max-width: 100%; height: auto;">
          </div>`;
          console.log(`Display math uploaded: ${s3Key}`);
        } else {
          throw new Error('Failed to fetch image');
        }
      } catch (error) {
        console.error(`Failed to process display math: ${error}`);
        // Fallback to Unicode
        mathReplacements[counter] = `<div style="text-align: center; margin: 15px 0; font-family: 'Times New Roman', serif; font-size: 1.2em;">
          ${convertMathToUnicode(match[1])}
        </div>`;
      }
    } else {
      // Fallback to Unicode
      mathReplacements[counter] = `<div style="text-align: center; margin: 15px 0; font-family: 'Times New Roman', serif; font-size: 1.2em;">
        ${convertMathToUnicode(match[1])}
      </div>`;
    }
    
    processedText = processedText.replace(match[0], placeholder);
    counter++;
  }
  
  // Replace inline math
  const inlineMatches = [...processedText.matchAll(/\$([^$\n]+)\$/g)];
  for (const match of inlineMatches) {
    const placeholder = `MATHIMG${counter}`;
    const imageUrl = await latexToImageUrl(match[1], false);
    
    if (imageUrl) {
      try {
        // Fetch the image
        const response = await fetch(imageUrl);
        if (response.ok) {
          const buffer = await response.buffer();
          
          // Upload to S3
          const filename = `math_${counter}.png`;
          const s3Key = `${reportFolder}/${filename}`;
          const s3Url = await uploadToS3(s3Key, buffer, 'image/png');
          
          mathReplacements[counter] = `<img src="${s3Url}" alt="${match[1]}" style="vertical-align: middle; height: 1.2em;">`;
          console.log(`Inline math uploaded: ${s3Key}`);
        } else {
          throw new Error('Failed to fetch image');
        }
      } catch (error) {
        console.error(`Failed to process inline math: ${error}`);
        // Fallback to Unicode
        mathReplacements[counter] = convertMathToUnicode(match[1]);
      }
    } else {
      // Fallback to Unicode
      mathReplacements[counter] = convertMathToUnicode(match[1]);
    }
    
    processedText = processedText.replace(match[0], placeholder);
    counter++;
  }
  
  // Render markdown to HTML
  let html = md.render(processedText);
  
  // Restore math images
  for (let i = 0; i < counter; i++) {
    html = html.replace(`MATHIMG${i}`, mathReplacements[i]);
  }
  
  return html;
}

// Helper to convert basic LaTeX to Unicode (fallback)
function convertMathToUnicode(latex) {
  let result = latex;
  
  // Handle fractions first
  result = result.replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, (match, num, den) => {
    // Recursively convert numerator and denominator
    const numConverted = convertMathToUnicode(num).replace(/<[^>]*>/g, '');
    const denConverted = convertMathToUnicode(den).replace(/<[^>]*>/g, '');
    return `${numConverted}/${denConverted}`;
  });
  
  // Handle square roots
  result = result.replace(/\\sqrt\{([^}]+)\}/g, (match, content) => {
    const converted = convertMathToUnicode(content).replace(/<[^>]*>/g, '');
    return `√(${converted})`;
  });
  
  // Handle subscripts and superscripts with braces
  result = result.replace(/\^{([^}]+)}/g, (match, exp) => {
    const superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻','n':'ⁿ','i':'ⁱ'};
    let converted = exp;
    for (const [char, sup] of Object.entries(superscripts)) {
      const escaped = char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      converted = converted.replace(new RegExp(escaped, 'g'), sup);
    }
    return converted;
  });
  
  result = result.replace(/_{([^}]+)}/g, (match, sub) => {
    const subscripts = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋','i':'ᵢ','n':'ₙ'};
    let converted = sub;
    for (const [char, sub] of Object.entries(subscripts)) {
      const escaped = char.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      converted = converted.replace(new RegExp(escaped, 'g'), sub);
    }
    return converted;
  });
  
  // Basic replacements for common math symbols
  const replacements = {
    '\\alpha': 'α', '\\beta': 'β', '\\gamma': 'γ', '\\delta': 'δ',
    '\\epsilon': 'ε', '\\theta': 'θ', '\\lambda': 'λ', '\\mu': 'μ',
    '\\pi': 'π', '\\sigma': 'σ', '\\phi': 'φ', '\\omega': 'ω',
    '\\infty': '∞', '\\partial': '∂', '\\nabla': '∇',
    '\\sum': '∑', '\\prod': '∏', '\\int': '∫',
    '\\pm': '±', '\\times': '×', '\\div': '÷',
    '\\leq': '≤', '\\geq': '≥', '\\neq': '≠',
    '\\approx': '≈', '\\equiv': '≡',
    '\\in': '∈', '\\notin': '∉', '\\subset': '⊂',
    '\\cup': '∪', '\\cap': '∩',
    '\\rightarrow': '→', '\\leftarrow': '←', '\\Rightarrow': '⇒',
    '\\cdot': '·', '\\dots': '…', '\\ldots': '…',
    '\\forall': '∀', '\\exists': '∃', '\\emptyset': '∅',
    '\\Re': 'ℜ', '\\Im': 'ℑ', '\\aleph': 'ℵ'
  };
  
  // Apply replacements
  for (const [tex, unicode] of Object.entries(replacements)) {
    result = result.replace(new RegExp(tex.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), unicode);
  }
  
  // Handle simple superscripts and subscripts without braces
  result = result.replace(/\^([0-9+\-ni])/g, (match, char) => {
    const superscripts = {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹','+':'⁺','-':'⁻','n':'ⁿ','i':'ⁱ'};
    return superscripts[char] || match;
  });
  
  result = result.replace(/_([0-9+\-ni])/g, (match, char) => {
    const subscripts = {'0':'₀','1':'₁','2':'₂','3':'₃','4':'₄','5':'₅','6':'₆','7':'₇','8':'₈','9':'₉','+':'₊','-':'₋','i':'ᵢ','n':'ₙ'};
    return subscripts[char] || match;
  });
  
  // Clean up remaining LaTeX commands we couldn't convert
  result = result.replace(/\\[a-zA-Z]+/g, '');
  
  // Clean up braces
  result = result.replace(/[{}]/g, '');
  
  return `<span style="font-family: 'Times New Roman', serif; font-size: 1.1em;">${result}</span>`;
}

// Helper to send email
async function sendEmail(subject, textBody, htmlBody, attachments = [], urgent = false) {
  // If we have attachments, we need to use SendRawEmailCommand
  if (attachments.length > 0) {
    
    // Build MIME message
    const mixedBoundary = `----=_Part_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const altBoundary = `----=_Alt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    let rawMessage = `From: ${config.emailFrom}\n`;
    rawMessage += `To: ${config.emailTo}\n`;
    
    // Add urgent headers if requested
    if (urgent) {
      rawMessage += `X-Priority: 1\n`;
      rawMessage += `X-MSMail-Priority: High\n`;
      rawMessage += `Priority: urgent\n`;
      rawMessage += `Importance: high\n`;
      rawMessage += `X-Mailer-Priority: 1\n`;
      rawMessage += `X-Gmail-Importance: 1\n`;
      rawMessage += `X-Google-Priority: High\n`;
    }
    rawMessage += `Subject: ${subject}\n`;
    rawMessage += `MIME-Version: 1.0\n`;
    rawMessage += `Content-Type: multipart/mixed; boundary="${mixedBoundary}"\n\n`;
    
    // Create multipart/alternative section for text/html
    rawMessage += `--${mixedBoundary}\n`;
    rawMessage += `Content-Type: multipart/alternative; boundary="${altBoundary}"\n\n`;
    
    // Add text part
    if (textBody) {
      rawMessage += `--${altBoundary}\n`;
      rawMessage += `Content-Type: text/plain; charset=UTF-8\n`;
      rawMessage += `Content-Transfer-Encoding: 7bit\n\n`;
      rawMessage += `${textBody}\n\n`;
    }
    
    // Add HTML part
    if (htmlBody) {
      rawMessage += `--${altBoundary}\n`;
      rawMessage += `Content-Type: text/html; charset=UTF-8\n`;
      rawMessage += `Content-Transfer-Encoding: 7bit\n\n`;
      rawMessage += `${htmlBody}\n\n`;
    }
    
    // Close alternative section
    rawMessage += `--${altBoundary}--\n\n`;
    
    // Add attachments
    for (const attachment of attachments) {
      rawMessage += `--${mixedBoundary}\n`;
      rawMessage += `Content-Type: ${attachment.contentType}\n`;
      rawMessage += `Content-Transfer-Encoding: base64\n`;
      rawMessage += `Content-Disposition: attachment; filename="${attachment.filename}"\n\n`;
      rawMessage += `${attachment.data}\n\n`;
    }
    
    rawMessage += `--${mixedBoundary}--`;
    
    const command = new SendRawEmailCommand({
      RawMessage: {
        Data: Buffer.from(rawMessage),
      },
    });
    
    await sesClient.send(command);
  } else if (urgent) {
    // No attachments but urgent - need raw email for headers
    let rawMessage = `From: ${config.emailFrom}\n`;
    rawMessage += `To: ${config.emailTo}\n`;
    rawMessage += `X-Priority: 1\n`;
    rawMessage += `X-MSMail-Priority: High\n`;
    rawMessage += `Priority: urgent\n`;
    rawMessage += `Importance: high\n`;
    rawMessage += `X-Mailer-Priority: 1\n`;
    rawMessage += `X-Gmail-Importance: 1\n`;
    rawMessage += `X-Google-Priority: High\n`;
    rawMessage += `Subject: ${subject}\n`;
    rawMessage += `MIME-Version: 1.0\n`;
    rawMessage += `Content-Type: multipart/alternative; boundary="simple-urgent-boundary"\n\n`;
    
    rawMessage += `--simple-urgent-boundary\n`;
    rawMessage += `Content-Type: text/plain; charset=UTF-8\n\n`;
    rawMessage += `${textBody}\n\n`;
    
    if (htmlBody) {
      rawMessage += `--simple-urgent-boundary\n`;
      rawMessage += `Content-Type: text/html; charset=UTF-8\n\n`;
      rawMessage += `${htmlBody}\n\n`;
    }
    
    rawMessage += `--simple-urgent-boundary--\n`;
    
    const command = new SendRawEmailCommand({
      Source: config.emailFrom,
      Destinations: [config.emailTo],
      RawMessage: {
        Data: rawMessage,
      },
    });
    
    await sesClient.send(command);
  } else {
    // No attachments, not urgent - use simple SendEmailCommand
    const command = new SendEmailCommand({
      Source: config.emailFrom,
      Destination: {
        ToAddresses: [config.emailTo],
      },
      Message: {
        Subject: { Data: subject },
        Body: {
          Text: textBody ? { Data: textBody } : undefined,
          Html: htmlBody ? { Data: htmlBody } : undefined,
        },
      },
    });
    
    await sesClient.send(command);
  }
}

// Create MCP server
const server = new Server(
  {
    name: 'report-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool: Send a report with text and optional images
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: 'send_report',
      description: 'Send a report with markdown-formatted content and optional files. MODE: If USABILIDE_REPORT_FOLDER environment variable is set to a path, saves reports locally to that folder (no email, no AWS required). If set to "EMAIL" or empty/unset, uses S3/SES cloud mode. LOCAL MODE: Organizes reports in {agent}/{YYYY-MM-DD}_{TAG}/ folders. CLOUD MODE: ALL images uploaded to S3 and displayed via URLs in email (guaranteed delivery). Up to 5 smallest images under 8MB total attached to email for convenience. SUPPORTS: Full markdown syntax AND LaTeX math equations using $ and $$. For complex LaTeX, use report_file parameter instead of text_content.',
      inputSchema: {
        type: 'object',
        properties: {
          agent_name: {
            type: 'string',
            description: 'Name of the agent sending the report',
          },
          title: {
            type: 'string',
            description: 'Report title',
          },
          text_content: {
            type: 'string',
            description: 'Report content in MARKDOWN format with optional LaTeX math. Use $ for inline math and $$ for display math. All standard markdown is supported: # headers, **bold**, *italic*, - lists, | tables |, ```code blocks```, etc. Either provide this OR report_file, not both.',
          },
          report_file: {
            type: 'string',
            description: 'Path to a markdown file containing the report content. Use this instead of text_content to avoid escaping issues with complex LaTeX. The file should contain markdown with optional LaTeX math equations.',
          },
          files: {
            type: 'array',
            description: 'Array of file paths to attach as supplementary files (images, data, etc.)',
            items: {
              type: 'string'
            },
          },
          urgent: {
            type: 'boolean',
            description: 'Mark email as urgent with high priority headers (X-Priority: 1, Priority: urgent, Importance: high)',
          },
        },
        required: ['agent_name', 'title'],
      },
    },
    {
      name: 'list_reports',
      description: 'List recent reports from S3. Can search by agent name, report tag, or date/time.',
      inputSchema: {
        type: 'object',
        properties: {
          agent_name: {
            type: 'string',
            description: 'Filter by agent name (optional)',
          },
          tag: {
            type: 'string',
            description: 'Filter by 4-character report tag (e.g., "AB12")',
          },
          date: {
            type: 'string',
            description: 'Filter by date in YYYY-MM-DD format (e.g., "2025-06-26")',
          },
          hour: {
            type: 'number',
            description: 'Filter by hour (0-23) in 24-hour format',
          },
          minute: {
            type: 'number',
            description: 'Filter by minute (0-59)',
          },
          max_results: {
            type: 'number',
            description: 'Maximum number of results (default 20)',
          },
          include_ancient: {
            type: 'boolean',
            description: 'Include ancient reports beyond the most recent 200 (default false)',
          },
        },
      },
    },
    {
      name: 'get_report',
      description: 'Get a specific report by its tag or by date/time. Returns the report URL and metadata.',
      inputSchema: {
        type: 'object',
        properties: {
          tag: {
            type: 'string',
            description: 'The 4-character report tag (e.g., "AB12")',
          },
          agent_name: {
            type: 'string',
            description: 'Agent name (required when searching by date/time)',
          },
          date: {
            type: 'string',
            description: 'Date in YYYY-MM-DD format (e.g., "2025-06-26")',
          },
          hour: {
            type: 'number',
            description: 'Hour (0-23) in 24-hour format',
          },
          minute: {
            type: 'number',
            description: 'Minute (0-59)',
          },
          include_ancient: {
            type: 'boolean',
            description: 'Include ancient reports beyond the most recent 200 (default false)',
          },
        },
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  if (name === 'send_report') {
    const { agent_name, title, text_content, report_file, files = [], urgent = false } = args;
    
    // Validate that only one of text_content or report_file is provided
    if ((text_content && report_file) || (!text_content && !report_file)) {
      return {
        content: [{
          type: 'text',
          text: 'Error: Provide either text_content OR report_file, not both and not neither.'
        }]
      };
    }
    
    // Get the report content either from string or file
    let reportContent;
    try {
      if (text_content) {
        reportContent = text_content;
      } else if (report_file) {
        reportContent = readFileSync(report_file, 'utf8');
      }
    } catch (error) {
      return {
        content: [{
          type: 'text',
          text: `Error reading report file: ${error.message}`
        }]
      };
    }

    // Auto-detect DISABLED - only use explicitly provided files
    // const autoDetectedFiles = [];
    // const filePattern = /(?:^|\s|["'`(])([\/~]?[.\w\-\/]+\.(py|sh))(?=\s|$|["'`),])/gm;
    // const matches = reportContent.matchAll(filePattern);

    // // Dependency directory patterns to exclude
    // const excludePatterns = [
    //   '/site-packages/',
    //   '/dist-packages/',
    //   '/node_modules/',
    //   '/.venv/',
    //   '/venv/',
    //   '/env/',
    //   '/.env/',
    //   '/miniconda3/',
    //   '/anaconda3/',
    //   '/lib/python',
    //   '/lib64/python',
    //   '/.conda/',
    // ];

    // for (const match of matches) {
    //   const mentionedPath = match[1];

    //   // Skip if already in files list
    //   if (files.includes(mentionedPath)) {
    //     continue;
    //   }

    //   // Try to resolve path (handle relative and absolute paths)
    //   let resolvedPath = mentionedPath;

    //   // If path starts with ~, replace with home directory
    //   if (mentionedPath.startsWith('~')) {
    //     resolvedPath = mentionedPath.replace(/^~/, process.env.HOME || '/home/ubuntu');
    //   }
    //   // If relative path, try from current working directory
    //   else if (!mentionedPath.startsWith('/')) {
    //     resolvedPath = join(process.cwd(), mentionedPath);
    //   }

    //   // Skip if path contains dependency directory patterns
    //   const isDependency = excludePatterns.some(pattern =>
    //     resolvedPath.includes(pattern) || mentionedPath.includes(pattern)
    //   );

    //   if (isDependency) {
    //     console.log(`Skipping dependency file: ${mentionedPath}`);
    //     continue;
    //   }

    //   // Check if file exists and add to auto-detected list
    //   try {
    //     const stats = statSync(resolvedPath);
    //     if (stats.isFile()) {
    //       // Check file size is reasonable (under 10MB)
    //       if (stats.size < 10 * 1024 * 1024) {
    //         autoDetectedFiles.push(resolvedPath);
    //         console.log(`Auto-detected mentioned file: ${mentionedPath} -> ${resolvedPath}`);
    //       }
    //     }
    //   } catch (error) {
    //     // File doesn't exist or can't be accessed, skip silently
    //   }
    // }

    // Only use explicitly provided files (no auto-detection)
    const allFiles = [...new Set([...files])]; // Use Set to remove duplicates

    const timestamp = new Date().toISOString();
    const reportTag = generateReportTag();
    const subject = `[${agent_name}] ${title} - Tag: ${reportTag}`;

    // Get hostname
    let hostname = 'unknown';
    try {
      hostname = execSync('hostname', { encoding: 'utf8' }).trim();
    } catch (e) {
      // Fallback if hostname command fails
    }

    // LOCAL MODE: Save to filesystem instead of S3/SES
    if (isLocalMode()) {
      const reportPath = createLocalReportFolder(agent_name, reportTag);
      const fileLinks = [];

      // Save all attached files locally
      for (const filePath of allFiles) {
        try {
          const content = readFileSync(filePath);
          const filename = basename(filePath);
          const localPath = join(reportPath, filename);

          // Save file
          saveToLocal(localPath, content);

          // Add to file links (just filename for relative paths in HTML)
          fileLinks.push({ filename });
        } catch (error) {
          console.error(`Failed to save ${filePath}:`, error);
        }
      }

      // Create HTML index page
      const indexHtml = createLocalReportIndex(agent_name, title, reportContent, fileLinks, timestamp, reportTag);
      const indexPath = join(reportPath, 'index.html');
      saveToLocal(indexPath, Buffer.from(indexHtml));

      // Create and save metadata JSON
      const date = new Date();
      const dateStr = date.toISOString().split('T')[0];
      const metadata = {
        tag: reportTag,
        agentName: agent_name,
        title: title,
        timestamp: timestamp,
        date: dateStr,
        hour: date.getHours(),
        minute: date.getMinutes(),
        reportPath: reportPath,
        indexPath: indexPath,
        hostname: hostname,
        mode: 'local'
      };
      const metadataPath = join(reportPath, 'metadata.json');
      saveToLocal(metadataPath, Buffer.from(JSON.stringify(metadata, null, 2)));

      // Get full path for user
      const fullIndexPath = join(config.localFolder, indexPath);

      return {
        content: [
          {
            type: 'text',
            text: `Report saved locally!\nReport Tag: ${reportTag}\nMode: LOCAL (no email sent)\nHostname: ${hostname}\nFiles saved: ${fileLinks.length}\nReport location: ${fullIndexPath}\n\nOpen in browser: file://${fullIndexPath}`,
          },
        ],
      };
    }

    // CLOUD MODE: Continue with S3/SES as normal
    // Sort files by size (smallest first) to maximize attachment count
    const sortedFiles = [...allFiles].sort((a, b) => {
      try {
        const sizeA = statSync(a).size;
        const sizeB = statSync(b).size;
        return sizeA - sizeB;
      } catch (error) {
        return 0;
      }
    });
    
    // Upload ALL files to S3 and collect for attachments
    const fileLinks = [];
    const emailAttachments = [];
    let attachmentBudget = 8 * 1024 * 1024; // 8MB safety limit for attachments
    const MAX_ATTACHMENTS = 5;

    // Collect text files for concatenation
    const textFiles = [];
    const textExtensions = ['.txt', '.csv', '.yaml', '.yml', '.json', '.py', '.sh', '.R', '.r',
                           '.js', '.ts', '.jsx', '.tsx', '.md', '.xml', '.html', '.css',
                           '.cpp', '.c', '.h', '.hpp', '.java', '.go', '.rs', '.rb',
                           '.php', '.sql', '.conf', '.ini', '.toml', '.env', '.log'];

    for (const filePath of sortedFiles) {
      try {
        const content = readFileSync(filePath);
        const filename = basename(filePath);
        const contentType = lookup(filename) || 'application/octet-stream';
        const key = generateS3Key(agent_name, filename);

        // Check if this is a text file
        const ext = filename.match(/\.[^.]+$/)?.[0]?.toLowerCase();
        const isTextFile = textExtensions.includes(ext) || contentType.startsWith('text/');

        if (isTextFile) {
          textFiles.push({
            path: filePath,
            filename: filename,
            content: content.toString('utf8')
          });
        }

        // ALWAYS upload to S3 first
        const url = await uploadToS3(key, content, contentType);
        fileLinks.push({ filename, url, size: content.length });

        // Try to add as email attachment if within budget
        if (isImage(filename) &&
            emailAttachments.length < MAX_ATTACHMENTS &&
            content.length < attachmentBudget) {
          emailAttachments.push({
            filename,
            url,
            contentType,
            data: content.toString('base64')
          });
          attachmentBudget -= content.length;
        }
      } catch (error) {
        console.error(`Failed to upload ${filePath}:`, error);
      }
    }

    // Create concatenated file if we have 2+ text files
    if (textFiles.length >= 2) {
      const delimiter = '=' .repeat(80);
      let concatenatedContent = `Combined Text Attachments\n${delimiter}\n`;
      concatenatedContent += `Total files: ${textFiles.length}\n`;
      concatenatedContent += `Generated at: ${new Date().toISOString()}\n`;
      concatenatedContent += `${delimiter}\n\n`;

      for (const textFile of textFiles) {
        concatenatedContent += `${delimiter}\n`;
        concatenatedContent += `FILE: ${textFile.filename}\n`;
        concatenatedContent += `PATH: ${textFile.path}\n`;
        concatenatedContent += `${delimiter}\n`;
        concatenatedContent += textFile.content;
        if (!textFile.content.endsWith('\n')) {
          concatenatedContent += '\n';
        }
        concatenatedContent += `\n`;
      }

      concatenatedContent += `${delimiter}\n`;
      concatenatedContent += `END OF COMBINED ATTACHMENTS\n`;
      concatenatedContent += `${delimiter}\n`;

      // Upload the concatenated file
      try {
        const concatenatedFilename = 'combined_text_attachments.txt';
        const concatenatedKey = generateS3Key(agent_name, concatenatedFilename);
        const concatenatedBuffer = Buffer.from(concatenatedContent, 'utf8');

        const concatenatedUrl = await uploadToS3(concatenatedKey, concatenatedBuffer, 'text/plain');
        fileLinks.push({
          filename: concatenatedFilename,
          url: concatenatedUrl,
          size: concatenatedBuffer.length,
          isCombined: true
        });

        console.log(`Created combined text file with ${textFiles.length} files`);
      } catch (error) {
        console.error('Failed to create combined text file:', error);
      }
    }
    
    // Create report folder key
    const date = new Date();
    const dateStr = date.toISOString().split('T')[0];
    const timeStr = date.toTimeString().split(' ')[0].replace(/:/g, '-');
    const reportFolder = `${agent_name}/${dateStr}_${timeStr}`;
    
    // Create HTML index page
    const indexHtml = createReportIndex(agent_name, title, reportContent, fileLinks, timestamp, reportTag);
    const indexKey = `${reportFolder}/index.html`;
    
    // Upload index page
    await uploadToS3(indexKey, Buffer.from(indexHtml), 'text/html');

    // Create and upload metadata JSON
    const metadata = {
      tag: reportTag,
      agentName: agent_name,
      title: title,
      timestamp: timestamp,
      date: dateStr,
      hour: date.getHours(),
      minute: date.getMinutes(),
      reportFolder: reportFolder,
      indexKey: indexKey,
      hostname: hostname
    };
    const metadataKey = `${reportFolder}/metadata.json`;
    await uploadToS3(metadataKey, Buffer.from(JSON.stringify(metadata, null, 2)), 'application/json');
    
    // Get URL for the index page
    const getIndexCommand = new GetObjectCommand({
      Bucket: config.bucketName,
      Key: indexKey,
    });
    const indexUrl = await getSignedUrl(s3Client, getIndexCommand, { 
      expiresIn: config.urlExpiration 
    });
    
    // Format time for email
    const emailDate = new Date(timestamp);
    const timeOptions = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
      timeZone: 'America/New_York',
      timeZoneName: 'short'
    };
    const formattedTime12h = emailDate.toLocaleString('en-US', timeOptions);
    
    // For 24-hour format in Eastern Time
    const time24Options = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: 'America/New_York',
      timeZoneName: 'short'
    };
    const formattedTime24h = emailDate.toLocaleString('en-US', time24Options);
    
    // Build email content with embedded images and full content
    const textBody = `Report from ${agent_name}
Report Tag: ${reportTag}
Hostname: ${hostname}

${reportContent}

${fileLinks.length > 0 ? `Attachments (${fileLinks.length}):\n${fileLinks.map(f => `- ${f.filename}`).join('\n')}\n\n` : ''}View full report:
${indexUrl}
`;
    
    // Build rich HTML email with embedded content
    let htmlBody = `
<div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
  <h2 style="color: #333;">Report from ${agent_name}</h2>
  <div style="color: #666; margin-bottom: 20px;">
    <div style="font-size: 1.2em; font-weight: bold; color: #0066cc; background: #e3f2fd; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-bottom: 10px;">Report Tag: ${reportTag}</div><br>
    <strong>Title:</strong> ${title}<br>
    <strong>Hostname:</strong> ${hostname}<br>
    <strong>Time (12-hour):</strong> ${formattedTime12h}<br>
    <strong>Time (24-hour):</strong> ${formattedTime24h}
  </div>
  
  <div style="background:#f5f5f5; padding:20px; border-radius:5px; margin-bottom:30px;">
    <h3 style="margin-top:0;">Report Content</h3>
    <div style="line-height: 1.6;">${await convertMarkdownToEmailHtmlWithImages(reportContent, agent_name, reportFolder)}</div>
  </div>
`;

    // Add ALL images via S3 URLs
    const imageFiles = fileLinks.filter(f => isImage(f.filename));
    if (imageFiles.length > 0) {
      htmlBody += `
  <div style="margin-bottom:30px;">
    <h3>Images (${imageFiles.length})</h3>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 15px;">
`;
      
      for (const img of imageFiles) {
        htmlBody += `
      <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: white;">
        <div style="font-weight: bold; margin-bottom: 10px;">${img.filename}</div>
        <img src="${img.url}" style="max-width: 100%; height: auto;" alt="${img.filename}">
        <div style="margin-top: 10px;">
          <a href="${img.url}" style="color: #0066cc;">View full size</a>
        </div>
      </div>
`;
      }
      
      htmlBody += `
    </div>
  </div>
`;
    }
    
    // Add file list if there are non-image files
    const nonImageFiles = fileLinks.filter(f => !isImage(f.filename));
    
    if (nonImageFiles.length > 0) {
      htmlBody += `
  <div style="margin-bottom:30px;">
    <h3>Other Attachments</h3>
    <ul style="list-style: none; padding: 0;">
`;
      
      for (const file of nonImageFiles) {
        htmlBody += `
      <li style="margin-bottom: 10px;">
         <a href="${file.url}" style="color: #0066cc;">${file.filename}</a>
      </li>
`;
      }
      
      htmlBody += `
    </ul>
  </div>
`;
    }
    
    // Add link to full report
    htmlBody += `
  <div style="margin-top:30px; padding-top:20px; border-top: 1px solid #ddd;">
    <a href="${indexUrl}" style="background:#0066cc; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; display:inline-block;">
      View Full Report in Browser
    </a>
  </div>
</div>
`;
    
    // Send email with selected images as attachments (up to 8MB total)
    await sendEmail(subject, textBody, htmlBody, emailAttachments, urgent);
    
    // Save the latest report URL to temp directory in working directory
    try {
      const tempDir = join(process.cwd(), 'temp');
      const urlFile = join(tempDir, 'latest-report-url.txt');
      
      // Create temp directory if it doesn't exist
      if (!existsSync(tempDir)) {
        mkdirSync(tempDir);
      }
      
      // Write the report URL (overwrites if exists)
      writeFileSync(urlFile, indexUrl);
    } catch (error) {
      // Silently ignore any errors - we don't want to break report sending
      console.error('Warning: Could not save latest report URL:', error.message);
    }
    
    // Append report reference to SCIENTIST.md if it exists
    try {
      const scientistPath = join(process.cwd(), 'SCIENTIST.md');
      if (existsSync(scientistPath)) {
        appendFileSync(scientistPath, `\n- [${reportTag}] ${title}\n`);
      }
    } catch (err) {
      console.error('Warning: Could not append report tag to SCIENTIST.md:', err.message);
    }
    
    const combinedFileCreated = textFiles.length >= 2;
    return {
      content: [
        {
          type: 'text',
          text: `Report sent successfully!\nReport Tag: ${reportTag}\nSubject: ${subject}\nHostname: ${hostname}\nFiles uploaded to S3: ${fileLinks.length}${combinedFileCreated ? ` (includes combined text file)` : ''}\nImages displayed via S3 URLs: ${imageFiles.length}\nImages attached to email: ${emailAttachments.length}\nReport URL: ${indexUrl}`,
        },
      ],
    };
  }
  
  if (name === 'list_reports') {
    const { agent_name, tag, date, hour, minute, max_results = 20, include_ancient = false } = args;
    
    // Determine how many objects to fetch (default 200 metadata files = ~600 total objects)
    const maxObjectsToFetch = include_ancient ? null : 600;
    
    // List metadata files with pagination
    const allObjects = [];
    let continuationToken = null;
    let totalFetched = 0;
    
    do {
      const command = new ListObjectsV2Command({
        Bucket: config.bucketName,
        Prefix: agent_name || '',
        MaxKeys: 1000,
        ContinuationToken: continuationToken,
      });
      
      const response = await s3Client.send(command);
      if (response.Contents) {
        allObjects.push(...response.Contents);
        totalFetched += response.Contents.length;
      }
      continuationToken = response.NextContinuationToken;
      
      // Stop if we've fetched enough for recent reports
      if (!include_ancient && maxObjectsToFetch && totalFetched >= maxObjectsToFetch) {
        break;
      }
    } while (continuationToken);
    
    // Filter for metadata.json files
    const metadataFiles = allObjects.filter(obj => obj.Key.endsWith('metadata.json'));
    const reports = [];
    
    // Fetch and parse metadata files
    for (const metaFile of metadataFiles) {
      try {
        const getCommand = new GetObjectCommand({
          Bucket: config.bucketName,
          Key: metaFile.Key,
        });
        const metaResponse = await s3Client.send(getCommand);
        const metaContent = await metaResponse.Body.transformToString();
        const metadata = JSON.parse(metaContent);
        
        // Apply filters
        let matches = true;
        if (tag && metadata.tag !== tag.toUpperCase()) matches = false;
        if (date && metadata.date !== date) matches = false;
        if (hour !== undefined && metadata.hour !== hour) matches = false;
        if (minute !== undefined && metadata.minute !== minute) matches = false;
        
        if (matches) {
          reports.push(metadata);
        }
      } catch (error) {
        console.error(`Error reading metadata ${metaFile.Key}:`, error);
      }
    }
    
    // Sort by timestamp descending
    reports.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    // Limit results
    const limitedReports = reports.slice(0, max_results);
    
    let result = `Found ${limitedReports.length} reports${reports.length > max_results ? ` (showing first ${max_results})` : ''}:\n\n`;
    
    for (const report of limitedReports) {
      const date = new Date(report.timestamp);
      const time12h = date.toLocaleString('en-US', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
        timeZone: 'America/New_York'
      });
      
      result += `Tag: ${report.tag} | ${report.agentName} - "${report.title}"\n`;
      result += `   Time: ${time12h}\n`;
      result += `   Path: ${report.indexKey}\n\n`;
    }
    
    if (limitedReports.length === 0) {
      result = 'No reports found matching the specified criteria.\n';
      if (tag) result += `Tag filter: ${tag}\n`;
      if (date) result += `Date filter: ${date}\n`;
      if (hour !== undefined) result += `Hour filter: ${hour}\n`;
      if (minute !== undefined) result += `Minute filter: ${minute}\n`;
    }
    
    return {
      content: [
        {
          type: 'text',
          text: result,
        },
      ],
    };
  }
  
  if (name === 'get_report') {
    const { tag, agent_name, date, hour, minute, include_ancient = false } = args;
    
    if (!tag && (!agent_name || !date || hour === undefined || minute === undefined)) {
      return {
        content: [{
          type: 'text',
          text: 'Error: Provide either a tag OR agent_name with date, hour, and minute.'
        }]
      };
    }
    
    // Determine how many objects to fetch
    // When searching by tag, we need to fetch ALL objects since S3 returns them alphabetically, not by date
    const maxObjectsToFetch = include_ancient ? null : (tag ? null : 600);
    
    // List metadata files with pagination
    const allObjects = [];
    let continuationToken = null;
    let totalFetched = 0;
    
    do {
      const command = new ListObjectsV2Command({
        Bucket: config.bucketName,
        Prefix: agent_name || '',
        MaxKeys: 1000,
        ContinuationToken: continuationToken,
      });
      
      const response = await s3Client.send(command);
      if (response.Contents) {
        allObjects.push(...response.Contents);
        totalFetched += response.Contents.length;
      }
      continuationToken = response.NextContinuationToken;
      
      // Stop if we've fetched enough for recent reports
      if (!include_ancient && maxObjectsToFetch && totalFetched >= maxObjectsToFetch) {
        break;
      }
    } while (continuationToken);
    
    // Filter for metadata.json files and sort by LastModified (newest first)
    const metadataFiles = allObjects
      .filter(obj => obj.Key.endsWith('metadata.json'))
      .sort((a, b) => {
        // Ensure we're comparing timestamps properly
        const timeA = a.LastModified ? new Date(a.LastModified).getTime() : 0;
        const timeB = b.LastModified ? new Date(b.LastModified).getTime() : 0;
        return timeB - timeA; // Newest first
      });
    
    // Search for matching report
    for (const metaFile of metadataFiles) {
      try {
        const getCommand = new GetObjectCommand({
          Bucket: config.bucketName,
          Key: metaFile.Key,
        });
        const metaResponse = await s3Client.send(getCommand);
        const metaContent = await metaResponse.Body.transformToString();
        const metadata = JSON.parse(metaContent);
        
        // Check if matches
        let matches = false;
        if (tag && metadata.tag === tag.toUpperCase()) {
          matches = true;
        } else if (date && hour !== undefined && minute !== undefined) {
          if (metadata.date === date && metadata.hour === hour && metadata.minute === minute) {
            matches = true;
          }
        }
        
        if (matches) {
          // Get URL for the report
          const getReportCommand = new GetObjectCommand({
            Bucket: config.bucketName,
            Key: metadata.indexKey,
          });
          const reportUrl = await getSignedUrl(s3Client, getReportCommand, { 
            expiresIn: config.urlExpiration 
          });
          
          const date = new Date(metadata.timestamp);
          const time12h = date.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
            timeZone: 'America/New_York',
            timeZoneName: 'short'
          });
          
          return {
            content: [{
              type: 'text',
              text: `Found report!\n\nTag: ${metadata.tag}\nAgent: ${metadata.agentName}\nTitle: ${metadata.title}\nTime: ${time12h}\n\nReport URL: ${reportUrl}`
            }]
          };
        }
      } catch (error) {
        console.error(`Error reading metadata ${metaFile.Key}:`, error);
      }
    }
    
    return {
      content: [{
        type: 'text',
        text: 'No report found matching the specified criteria.'
      }]
    };
  }
  
  throw new Error(`Unknown tool: ${name}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('Report MCP Server running...');

  if (isLocalMode()) {
    console.error(`Mode: LOCAL (filesystem storage)`);
    console.error(`Local folder: ${config.localFolder}`);
    console.error(`NOTE: Reports will be saved locally. No S3 upload, no email sending.`);
  } else {
    console.error(`Mode: CLOUD (S3 + SES)`);
    console.error(`Bucket: ${config.bucketName}`);
    console.error(`Region: ${config.region}`);
    console.error(`Email: ${config.emailFrom} -> ${config.emailTo}`);
  }
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});