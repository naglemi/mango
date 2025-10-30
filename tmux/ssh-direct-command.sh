#!/bin/bash

# Generate TOTP
TOTP=$(oathtool --totp=SHA1 --base32 "AJW3D7MUBZGYE2B6SK6V6NCFL3S4Q2SV" 2>/dev/null)
echo "TOTP: $TOTP"

# Try using SSH with command directly
echo "Attempting direct SSH with command..."
ssh -tt -i ~/.ssh/id_rsa_expanse -o StrictHostKeyChecking=no naglemi@login.expanse.sdsc.edu "sacct -u naglemi --state=RUNNING --format=JobID,JobName,NodeList --noheader"