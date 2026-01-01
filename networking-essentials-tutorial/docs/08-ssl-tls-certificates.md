# Module 8: SSL/TLS Certificates

## What SSL/TLS Actually Encrypts

Your HTTPS request goes through an encrypted tunnel. The encryption is SSL/TLS (they're related: SSL is older, TLS is newer, people use them interchangeably).

```
Without TLS:
  Client → [password123] → Hacker → Server
  (visible on network)

With TLS:
  Client → [encrypted gibberish] → Hacker → Server
  (hacker can't read it without key)
```

What TLS **does** encrypt:

```
✓ Request body          (POST data, form submissions)
✓ Response body         (API responses, HTML)
✓ Headers              (except first line)
✓ Cookies              (session data)
```

What TLS **doesn't** encrypt:

```
✗ Which domain you're visiting  (Hacker sees example.com in DNS)
✗ Request method (GET/POST visible)
✗ Path                  (hacker sees /api/users)
✗ Which ports are open  (network scanning)
```

## How TLS Works (Simplified)

### Three Phases

#### 1. Handshake (Establish Encryption)

```
Client: "Hi, I want to talk securely"
Server: "OK, here's my certificate proving who I am"
Client: "I verified you. Here's an encryption key"
Server: "Confirmed, we're encrypted now"
```

This takes ~100ms. Then actual communication is encrypted.

#### 2. Communication (Send Encrypted Data)

```
Client: [ENCRYPTED GET /api/users]
Server: [ENCRYPTED {"users": [...]}]
```

Both sides have the shared encryption key from handshake.

#### 3. Closure (End Connection)

```
Client or Server: [ENCRYPTED goodbye]
Connection closes
```

### Key Concepts

**Symmetric encryption** (both have same key):

```
Encryption Key: 0xA1B2C3D4
Client: Uses 0xA1B2C3D4 to encrypt
Server: Uses 0xA1B2C3D4 to decrypt

Problem: How do you share this key securely?
Answer: Use RSA (below)
```

**Asymmetric encryption** (public/private key pair):

```
Server has two keys:
  Public Key:  Shared with world (in certificate)
  Private Key: Secret, never shared

Client: Encrypts data with server's Public Key
Server: Decrypts data with its Private Key

Only server can decrypt (has private key)
```

During handshake, this is used to exchange the symmetric key securely.

## Certificates: Proving Your Identity

A certificate is a file that says "I am example.com" and is signed by a trusted authority.

### Certificate Contents

```
Certificate {
    Subject: CN=example.com
    Issuer: C=US, O=Let's Encrypt, CN=R3
    Public Key: [long key string]
    Valid From: 2023-01-01
    Valid Until: 2024-01-01
    Signature: [signed by Let's Encrypt]
}
```

### Certificate Chain

Your cert is signed by an intermediate cert, which is signed by a root cert.

```
Your Certificate (example.com)
     ↓ signed by
Intermediate Certificate (Let's Encrypt R3)
     ↓ signed by
Root Certificate (ISRG Root X1)
     ↓
Client's browser has Root in trust store
     ↓
Browser verifies: Root signed Intermediate,
Intermediate signed Your Cert
     ↓
✓ Certificate valid!
```

This is why your Nginx config has two files:

```nginx
ssl_certificate /path/to/fullchain.pem;        # Your cert + intermediate
ssl_certificate_key /path/to/privkey.pem;      # Your private key
```

`fullchain.pem` = your certificate + intermediates (complete chain)

### Root Certificates

Your browser ships with ~150 root certificates from trusted authorities.

```
When browser gets an HTTPS response:
1. Receives server's certificate
2. Checks: Is this cert signed by one of my trusted roots?
3. If yes: ✓ Trusted, proceed
4. If no: ✗ Untrusted, show warning
```

This prevents someone from creating fake certificates for example.com (they'd need to be signed by a root you trust).

## Getting Certificates: Let's Encrypt

Let's Encrypt is a free, automated certificate authority.

### Installation

```bash
# Install certbot (Let's Encrypt client)
sudo apt update
sudo apt install certbot python3-certbot-nginx python3-certbot-apache

# or manual installation
sudo apt install certbot
```

### Obtaining Certificate

```bash
# Standalone mode (Nginx/Apache not needed)
sudo certbot certonly --standalone -d example.com -d www.example.com

# With Nginx (certbot modifies nginx.conf)
sudo certbot --nginx -d example.com

# With Apache
sudo certbot --apache -d example.com
```

Certbot verifies you own the domain by:

```
1. You prove control of example.com domain
   (Usually by responding to HTTP request on :80)

2. Let's Encrypt issues certificate
   (Valid for 90 days)

3. Certificate saved at:
   /etc/letsencrypt/live/example.com/
```

### Auto-Renewal

Let's Encrypt certs expire in 90 days.

```bash
# Set up auto-renewal
sudo certbot renew --dry-run  # Test
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer

# Renewal runs automatically (usually daily)
```

Or manually:

```bash
# Renew expiring certificates
sudo certbot renew

# Renew specific domain
sudo certbot renew -d example.com
```

## Manual Certificate Management

If not using Nginx/Apache:

### Using Certbot Standalone

```bash
# Get certificate (without Nginx)
sudo certbot certonly --standalone -d example.com

# Certificates stored at
/etc/letsencrypt/live/example.com/
  ├── cert.pem        (your certificate)
  ├── chain.pem       (intermediate chain)
  ├── fullchain.pem   (cert + chain together)
  └── privkey.pem     (your private key)
```

### Using Certbot DNS Challenge

If you can't verify via HTTP, use DNS:

```bash
# DNS challenge (you add TXT record to DNS)
sudo certbot certonly --dns-cloudflare -d example.com

# Cloudflare API token needed
# Other providers: --dns-route53, --dns-google, etc.

# Certbot waits while you add DNS record
# Let's Encrypt verifies the record
# Issues certificate
```

## Nginx TLS Configuration

### Minimal Setup

```nginx
server {
    listen 443 ssl;
    server_name example.com;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### Recommended Production Setup

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;
    
    # Certificates
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # TLS versions (disable old, slow protocols)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    # Strong ciphers
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    
    # Enable HSTS (browsers always use HTTPS)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Performance
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### HTTP to HTTPS Redirect

```nginx
# Redirect all HTTP to HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}

# Handle HTTPS
server {
    listen 443 ssl;
    server_name example.com;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

## TLS Termination vs End-to-End Encryption

### TLS Termination (Recommended)

```
Client → HTTPS ──→ Nginx (TLS termination, decrypts)
                    ↓
                   HTTP (internal, no encryption)
                    ↓
                   Flask (plain HTTP)

Advantages:
✓ Nginx is fast at TLS
✓ Simple to manage certificates (one place)
✓ Less CPU on backend servers
✓ Can inspect/cache/modify requests in Nginx

Disadvantages:
✗ Internal traffic not encrypted (less critical)
```

### End-to-End Encryption

```
Client → HTTPS ──→ Nginx (doesn't decrypt)
                    ↓
                   HTTPS
                    ↓
                   Flask (decrypts and handles HTTPS)

Advantages:
✓ All traffic encrypted (paranoid security)

Disadvantages:
✗ More CPU on backend servers
✗ Harder to manage certs on every backend
✗ Can't cache or inspect in Nginx
✗ Slower overall
```

**For most backends**: Use TLS termination at Nginx.

## Common Certificate Issues

### Issue 1: Certificate Expired

```
Error: SSL_ERROR_RX_RECORD_TOO_LONG
Or: Your connection is not secure

Cause: Certificate expiration date passed
Solution: Renew with certbot renew
```

Check expiration:

```bash
# Check certificate expiration
openssl x509 -in /etc/letsencrypt/live/example.com/cert.pem -text -noout | grep "Not After"

# Or
certbot certificates

# Find expiring soon
certbot certificates | grep "EXPIRES"
```

### Issue 2: Certificate Mismatch

```
Error: Subject Alternative Name doesn't match requested host name
Or: Certificate is for example.com, not www.example.com

Cause: Certificate doesn't include all domains
Solution: Regenerate with all domains:
  certbot certonly -d example.com -d www.example.com
```

Check cert domains:

```bash
openssl x509 -in /path/to/cert.pem -text -noout | grep -A 1 "Subject Alternative Name"
```

### Issue 3: Self-Signed Certificate Warning

```
Error: Subject is example.com, Issuer is also example.com
Or: This site is not secure

Cause: Certificate is self-signed (signed by yourself, not trusted CA)
Solution: Get certificate from Let's Encrypt
```

For testing only:

```bash
# Generate self-signed cert (testing only!)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Use in Nginx
ssl_certificate /path/to/cert.pem;
ssl_certificate_key /path/to/key.pem;

# In production: Get real certificate from Let's Encrypt
```

### Issue 4: Mixed Content Warning

```
Error: Insecure content from http:// loaded from https:// page

Cause: HTTPS page contains resources from HTTP URLs
Solution: Change all resources to HTTPS or protocol-relative URLs
```

Example:

```html
<!-- Wrong: Mixes HTTP and HTTPS -->
<script src="http://cdn.example.com/script.js"></script>

<!-- Right: Protocol-relative (uses same protocol as page) -->
<script src="//cdn.example.com/script.js"></script>

<!-- Also right: Explicit HTTPS -->
<script src="https://cdn.example.com/script.js"></script>
```

## TLS Security Headers

Headers that tell browsers how to be secure:

```nginx
# Force HTTPS for future requests (30 days)
add_header Strict-Transport-Security "max-age=2592000" always;

# Prevent clickjacking (don't display in frame)
add_header X-Frame-Options "DENY" always;

# Don't guess content type (use what server says)
add_header X-Content-Type-Options "nosniff" always;

# Enable XSS protection
add_header X-XSS-Protection "1; mode=block" always;
```

## Production Checklist

Before going live with HTTPS:

- [ ] Certificate obtained from trusted CA (Let's Encrypt)
- [ ] Certificate covers all domains (example.com, www.example.com, api.example.com)
- [ ] Certificate not expiring soon (at least 30 days)
- [ ] Auto-renewal configured
- [ ] Nginx redirects HTTP to HTTPS
- [ ] TLS 1.2+ enabled, TLS 1.0/1.1 disabled
- [ ] Strong cipher suites configured
- [ ] HSTS header set
- [ ] All internal resources HTTPS or protocol-relative
- [ ] Mixed content warnings resolved
- [ ] Security headers set (X-Frame-Options, X-Content-Type-Options)
- [ ] Tested with SSL Labs (https://www.ssllabs.com/ssltest/)

## Monitoring Certificate Expiration

```bash
#!/bin/bash
# Check cert expiration (add to cron)

CERT_FILE="/etc/letsencrypt/live/example.com/cert.pem"
DAYS_LEFT=$(( ($(date -d "$(openssl x509 -in $CERT_FILE -noout -enddate | cut -d= -f2)" +%s) - $(date +%s)) / 86400 ))

if [ $DAYS_LEFT -lt 30 ]; then
    echo "Certificate expires in $DAYS_LEFT days - RENEW SOON"
    # Send alert
fi
```

## Backend Code: Secure Cookies

When you set cookies over HTTPS, mark them secure:

```python
from flask import Flask, make_response

@app.route('/login')
def login():
    response = make_response({'status': 'logged in'})
    response.set_cookie(
        'session_id',
        'abc123xyz',
        secure=True,        # Only sent over HTTPS
        httponly=True,      # Not accessible from JavaScript
        samesite='Strict'   # CSRF protection
    )
    return response
```

The `secure` flag means:

```
Browser: Only send this cookie over HTTPS
         Never send it over HTTP
         
If someone mans-in-the-middle HTTP, they won't get the cookie
```

---

## Module 8 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. What does TLS encryption protect from?
   a) DDoS attacks
   b) Someone on the network reading your data
   c) Server being hacked
   d) DNS spoofing

2. A certificate is signed by an intermediate, which is signed by root. Why this chain?
   a) More secure than single cert
   b) Allows browsers to verify without downloading all root keys
   c) Required by browsers
   d) Makes encryption stronger

3. Let's Encrypt certificate expires in 90 days. When should you renew?
   a) On expiration day
   b) Days before expiration
   c) Automatically with certbot
   d) Never, just get new cert

4. Your Nginx receives HTTPS but forwards HTTP to Flask. Is this secure?
   a) No, data is unencrypted internally
   b) Yes, TLS termination is standard practice
   c) No, Flask should handle HTTPS
   d) Depends on network setup

5. You set cookie with secure=True. What happens over HTTP?
   a) Cookie is encrypted
   b) Cookie is sent as normal
   c) Browser won't send cookie over HTTP
   d) Cookie is not set

### Practical Networking Tasks

**Task 1: Obtain Real Certificate**

- Register free domain (freenom.com) or use existing one
- Install certbot
- Obtain Let's Encrypt certificate:
  ```bash
  sudo certbot certonly --standalone -d your-domain.com
  ```
- Check certificate details:
  ```bash
  openssl x509 -in /etc/letsencrypt/live/your-domain/cert.pem -text -noout
  ```
- Verify chain:
  ```bash
  openssl x509 -in /etc/letsencrypt/live/your-domain/chain.pem -text -noout
  ```

**Task 2: Nginx with HTTPS**

- Configure Nginx reverse proxy with your certificate
- Set up HTTP → HTTPS redirect
- Configure TLS best practices (strong ciphers, TLS 1.2+)
- Test with curl:
  ```bash
  curl -i https://your-domain.com/
  curl https://your-domain.com/  # No HTTPS redirect
  curl http://your-domain.com/   # Should redirect to https
  ```
- Verify with SSL Labs or similar tool

### Production Incident Scenario

**Incident**: Users report "Your connection is not secure" warnings. Investigation shows:

```
Domain:      example.com
Certificate: issued for *.example.com
User visits: api.example.com
Browser: ✓ Matches (subdomain wildcard)

User visits: staging.api.example.com
Browser: ✗ Doesn't match (two subdomains too deep)

User visits: www.example.com
Browser: ✗ Doesn't match (certificate missing www)
```

Certificate only covers `*.example.com` but not bare `example.com` or nested subdomains.

Questions:

1. What went wrong in certificate issuance?
2. Which domains should the certificate include?
3. How would you fix this?
4. How do you prevent this in future?
5. Can you renew without downtime?

---

**Next**: [Module 9: Final Project](09-final-project.md)
