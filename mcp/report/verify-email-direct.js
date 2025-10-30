#!/usr/bin/env node

import { SESClient, VerifyEmailIdentityCommand, GetIdentityVerificationAttributesCommand } from '@aws-sdk/client-ses';

const client = new SESClient({ region: 'us-east-1' });
const email = 'slurmalerts1017@gmail.com';

async function verifyEmail() {
  try {
    // Send verification email
    console.log(` Sending verification email to ${email}...`);
    
    const verifyCommand = new VerifyEmailIdentityCommand({
      EmailAddress: email
    });
    
    await client.send(verifyCommand);
    console.log(' Verification email sent successfully!');
    console.log('');
    console.log('  CHECK YOUR EMAIL NOW!');
    console.log(`   Email sent to: ${email}`);
    console.log('   Subject: "Amazon Web Services – Email Address Verification Request"');
    console.log('   From: no-reply-aws@amazon.com');
    console.log('');
    console.log('   Click the verification link in that email!');
    
    // Check current status
    console.log('\nChecking current verification status...');
    const statusCommand = new GetIdentityVerificationAttributesCommand({
      Identities: [email]
    });
    
    const response = await client.send(statusCommand);
    console.log('Current status:', response.VerificationAttributes);
    
  } catch (error) {
    console.error(' Error:', error.message);
  }
}

verifyEmail();