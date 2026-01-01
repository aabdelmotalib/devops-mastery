# Module 7: DNS and Domain Management

## How DNS Actually Works

Your browser needs to find your server. DNS (Domain Name System) translates domain names to IP addresses.

```
User types: https://example.com
Browser: "Where is example.com?"
DNS Resolver: "That's 203.0.113.45"
Browser: Connects to 203.0.113.45
```

## DNS Resolution Process

### Step-by-Step

```
1. Browser asks local resolver: "Where is example.com?"
   Local resolver: Check local cache (ISP resolver)

2. If not cached, ask root nameserver: "Where is .com?"
   Root: "Ask Verisign (manages .com)"

3. Ask Verisign: "Where is example.com?"
   Verisign: "Ask these nameservers (set in domain registrar)"

4. Ask example.com's nameservers: "Where is example.com?"
   Nameserver: "That's 203.0.113.45"

5. Browser gets IP, connects to 203.0.113.45
```

### Caching

DNS results are cached to avoid this lookup every time.

```
First request: Lookup takes ~300ms
Second request: Cache hit, takes ~1ms

Cache stored at:
- Browser cache (minutes)
- ISP resolver cache (hours)
- Registrar's nameserver (TTL-determined)
```

## DNS Records

Different record types tell DNS what to do.

### A Record (IP Address for IPv4)

```
example.com    A    203.0.113.45

Means: example.com points to IP 203.0.113.45
```

### AAAA Record (IP Address for IPv6)

```
example.com    AAAA    2001:db8::1

Means: example.com points to IPv6 address 2001:db8::1
```

### CNAME Record (Canonical Name - Alias)

```
www.example.com    CNAME    example.com

Means: www.example.com is an alias for example.com
Client resolves www.example.com → example.com → 203.0.113.45
```

Use CNAMEs for:

```
www.example.com      → example.com (main site)
blog.example.com     → blog.example.com-external.platform.com (hosted blog)
api.example.com      → api-lb.example.internal (internal load balancer)
```

### MX Record (Mail Exchange)

```
example.com    MX    10    mail.example.com
example.com    MX    20    mail2.example.com

Means: Send mail for example.com to mail.example.com (priority 10)
       If that fails, try mail2.example.com (priority 20)
```

### TXT Record (Text)

```
example.com    TXT    "v=spf1 include:_spf.google.com ~all"

Means: Custom text record (often used for authentication)
```

Common uses:

```
SPF:     Prevent email spoofing
DKIM:    Sign outgoing emails
DMARC:   Email authentication policy
```

### NS Record (Nameserver)

```
example.com    NS    ns1.example.com
example.com    NS    ns2.example.com

Means: These servers are authoritative for example.com
```

Set by registrar when you configure nameservers.

## TTL (Time To Live)

Controls how long DNS results are cached.

```
example.com    A    203.0.113.45    TTL=3600

Means: Cache this result for 3600 seconds (1 hour)
       After 1 hour, ask nameserver again
```

### TTL Values

```
300 seconds (5 min)      - Frequently changing (temporary setups)
3600 seconds (1 hour)    - Normal (most common)
86400 seconds (1 day)    - Stable (rarely changes)
```

### Changing DNS Records

You want to change your IP. Problem: old cached entries still point to old IP.

```
Scenario: Move to new server

Old setup:
  example.com    A    203.0.113.45 (old server)

You want:
  example.com    A    203.0.113.46 (new server)

But users still have cached 203.0.113.45

Solution:
1. Lower TTL 1 day before change (TTL=300)
   Reduces cache time to 5 minutes
2. Update DNS record
3. Within 5 minutes, all users see new IP
4. After change settled, raise TTL back to 3600
```

## Backend Use: Setting Up Your Domain

### Registrar Configuration

When you buy example.com from a registrar (GoDaddy, Namecheap, etc.):

```
1. Registrar asks: "Which nameservers should manage this domain?"

2. You choose:
   Option A: Use registrar's nameservers (usually default)
   Option B: Use external nameservers (Route 53, Cloudflare, etc.)

3. Registrar updates root nameservers to point to your chosen nameservers

4. Your nameserver must define all records (A, MX, CNAME, etc.)
```

### DNS Hosting Providers

Common choices:

```
Route 53 (AWS):        Full control, integrated with AWS
Cloudflare:            Free tier, DDoS protection
DNSimple:              Simple interface
Google Domains:        Integrated with Google services
Your registrar:        Usually free, often simpler interface
```

### Setting Up with Cloudflare (Example)

```
1. Sign up for Cloudflare
2. Add site: example.com
3. Cloudflare tells you: "Update nameservers at your registrar to:"
   ns1.cloudflare.com
   ns2.cloudflare.com

4. Go to your registrar, set nameservers to those
   (Wait up to 24 hours for propagation)

5. In Cloudflare dashboard, create records:
   Type A:  example.com → 203.0.113.45
   Type A:  www → 203.0.113.45
   Type CNAME: api → api-lb.internal
```

## DNS Commands (Debugging)

### nslookup (Query DNS)

```bash
nslookup example.com

# Output:
# Server:  8.8.8.8 (Google's DNS)
# Address: 8.8.8.8#53
#
# Name:    example.com
# Address: 203.0.113.45
```

Query specific nameserver:

```bash
nslookup example.com ns1.cloudflare.com
```

### dig (Detailed DNS info)

```bash
dig example.com

# Output:
# ; <<>> DiG 9.10.6 <<>> example.com
# ...
# example.com.    3600    IN    A    203.0.113.45
```

Get specific record type:

```bash
dig example.com MX
# Returns MX records

dig example.com TXT
# Returns TXT records

dig example.com NS
# Returns nameservers
```

### host (Simple lookup)

```bash
host example.com

# Output:
# example.com has address 203.0.113.45
# example.com mail is handled by 10 mail.example.com.
```

### Reverse DNS Lookup

Find domain from IP:

```bash
nslookup 203.0.113.45

# Output:
# 45.113.0.203.in-addr.arpa    name = example.com.

# Useful for: Checking if server is properly set up
```

## DNS for Backends

### Single Domain → Single Server

```
example.com    A    203.0.113.45

Request: https://example.com/api/users
Resolves to: 203.0.113.45
```

### Multiple Subdomains

```
example.com       A    203.0.113.45    (main site)
api.example.com   A    203.0.113.45    (same server)
cdn.example.com   A    203.0.113.46    (CDN server)
mail.example.com  A    203.0.113.47    (mail server)
```

### Failover (Redundancy)

Problem: One IP fails

```
Single A record:
  example.com    A    203.0.113.45
  
  If 203.0.113.45 goes down, everyone fails

Solution: Multiple A records
  example.com    A    203.0.113.45    (Primary)
  example.com    A    203.0.113.46    (Secondary)
  
  DNS returns both IPs
  Browser tries first, if fails, tries second
```

Most DNS providers support this:

```
Cloudflare:   Create two A records with same name
Route 53:     Create A record with multiple values
```

### Weighted Round-Robin

```
example.com    A    203.0.113.45    (weight 70%)
example.com    A    203.0.113.46    (weight 30%)

70% of traffic to server 45
30% of traffic to server 46

Useful for: Gradual traffic migration
```

### Geo-Routing

```
example.com (US)       A    203.0.113.45 (US server)
example.com (Europe)   A    203.0.113.46 (Europe server)
example.com (Asia)     A    203.0.113.47 (Asia server)

Users in different regions get different IPs
Reduces latency
```

Providers: CloudFlare, Route 53, Akamai, etc.

## Common DNS Mistakes

### Mistake 1: Wrong Nameservers

```
Problem: Domain registrar still points to old nameservers
Result: Changes you make don't apply

Example:
  You use Cloudflare nameservers
  Add A record in Cloudflare: example.com → 203.0.113.45
  But users still see old IP
  
Cause: Registrar still points to old nameserver
  example.com    NS    old-ns.oldprovider.com
  (Not Cloudflare)
  
Solution:
  Update nameservers at registrar to point to Cloudflare
```

Check nameservers:

```bash
dig example.com NS

# Shows which nameservers are authoritative
# Compare with what your DNS provider shows
```

### Mistake 2: TTL Too High

```
problem: Want to change IP, but DNS cached for 24 hours

Setup:
  example.com    A    203.0.113.45    TTL=86400 (24 hours)

User visits at 1:00 PM
  → Gets 203.0.113.45
  → Cached locally

You change to 203.0.113.46 at 2:00 PM
  
User revisits at 2:30 PM
  → Still gets cached 203.0.113.45
  → Won't get new IP until 1:00 PM next day!

Solution: Lower TTL before change
  2 days before change: Set TTL=300 (5 min)
  Make change
  Wait 5 minutes for propagation
  Set TTL back to 86400
```

### Mistake 3: Not Creating www Subdomain

```
Problem: example.com works, www.example.com doesn't

Solution:
  example.com    A    203.0.113.45
  www            A    203.0.113.45    (or CNAME to example.com)

Or even better:
  example.com    A    203.0.113.45
  www            CNAME example.com.
```

### Mistake 4: Forgetting MX Records

```
Problem: Email doesn't work for your domain

Solution: Set MX records

example.com    MX    10    mail.example.com.
mail           A           203.0.113.47

or use email provider:

example.com    MX    10    mail.google.com.
               MX    20    mail2.google.com.
```

### Mistake 5: DNS Propagation Confusion

```
Change DNS record → Expect immediate change
But propagation takes time (up to 24-48 hours)

Why?
- Root nameservers updated first
- Then registrars
- Then ISP resolvers
- Then client caches

Different parts of internet see different values temporarily
```

Solution: Be patient and lower TTL beforehand.

## DNS Security

### SPF (Sender Policy Framework)

Prevent email spoofing:

```
example.com    TXT    "v=spf1 include:_spf.google.com ~all"

Means: Only Google's mail servers can send from example.com
       Other servers will be marked as spam
```

### DKIM (DomainKeys Identified Mail)

Sign outgoing emails:

```
default._domainkey.example.com    TXT    "v=DKIM1; k=rsa; p=MIGfMA0BGQ..."

Means: Emails from example.com are signed with this key
       Recipients verify signature came from example.com
```

### DMARC (Domain-based Message Authentication)

```
_dmarc.example.com    TXT    "v=DMARC1; p=reject; rua=mailto:admin@example.com"

Means: If SPF/DKIM fail, reject the email
       Send reports to admin@example.com
```

## Debugging DNS Issues

### Issue: Domain Points to Wrong IP

```bash
# Check what DNS says
dig example.com

# If wrong, check nameserver authority
dig @ns1.cloudflare.com example.com

# Verify record at your DNS provider's dashboard
# Sometimes dashboard shows correct, but server doesn't

# Force check with public DNS
nslookup example.com 8.8.8.8
nslookup example.com 1.1.1.1
```

### Issue: DNS Cached Incorrectly

```bash
# Flush DNS cache (varies by OS)

# Linux
sudo systemctl restart systemd-resolved

# macOS
sudo killall -HUP mDNSResponder

# Windows
ipconfig /flushdns
```

### Issue: Slow DNS Resolution

```bash
# Measure DNS lookup time
time nslookup example.com

# If slow, try different resolver
time nslookup example.com 8.8.8.8

# If Google's is fast, your ISP's resolver is slow
# Use public DNS (8.8.8.8, 1.1.1.1, etc.)
```

## Production Notes

### 1. Multiple Nameservers

Always have redundancy:

```
example.com    NS    ns1.example.com.
example.com    NS    ns2.example.com.
example.com    NS    ns3.example.com.

If one nameserver fails, others still respond
```

### 2. Health Monitoring

Monitor your DNS:

```bash
# Script to check DNS
while true; do
  dig example.com +short
  sleep 300  # Check every 5 minutes
done

# Alert if unexpected IP
```

### 3. DNSSEC (Signed DNS)

Prevent DNS hijacking:

```
# Enable DNSSEC at your DNS provider
# Signs all records with private key
# Clients verify signature with public key
```

### 4. Graceful IP Migration

```
Day 1: Lower TTL to 300
       example.com    A    203.0.113.45    TTL=300

Day 2: Update DNS
       example.com    A    203.0.113.46    TTL=300

Day 3: Wait 5 minutes for propagation
       Verify traffic on new IP

Day 4: Raise TTL back
       example.com    A    203.0.113.46    TTL=3600
```

---

## Module 7 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. What does TTL=3600 mean?
   a) Cache for 3600 bytes
   b) DNS record valid for 3600 seconds
   c) 3600 DNS servers responsible
   d) IP changes every 3600 seconds

2. You set www.example.com as CNAME to example.com. User visits www.example.com. How many DNS lookups occur?
   a) One (direct lookup)
   b) Two (CNAME redirect means extra lookup)
   c) Three (root + registrar + nameserver)
   d) Depends on TTL

3. You change your A record from 203.0.113.45 to 203.0.113.46. Some users still reach old IP hours later. Why?
   a) DNS broken
   b) Record change didn't propagate
   c) Old TTL caused caching
   d) Root nameserver is slow

4. Your email stops working. MX records point to correct server. Check first:
   a) A record for mail server exists
   b) SPF record
   c) DKIM signature
   d) All of above

5. What is reverse DNS used for?
   a) Looks up IP to find domain
   b) Encrypts DNS queries
   c) Routes requests backwards
   d) Redundant nameserver

### Practical Networking Tasks

**Task 1: DNS Lookup Practice**

- Use dig to find DNS records:
  ```bash
  dig google.com
  dig google.com A
  dig google.com MX
  dig google.com TXT
  ```
- Find nameservers:
  ```bash
  dig example.com NS
  ```
- Query specific nameserver:
  ```bash
  dig @8.8.8.8 example.com
  ```
- Do reverse DNS:
  ```bash
  nslookup 8.8.8.8
  ```
- Document results

**Task 2: Set Up Domain Records**

- Get a test domain (or use local hosts file)
- Create/simulate these records:
  - A record: example.local → 192.168.1.100
  - CNAME: www → example.local
  - MX: mail → mail.example.local
- Verify with dig/nslookup

### Production Incident Scenario

**Incident**: Your new server is ready at 203.0.113.46. You updated DNS to point to it. But 30% of users still can't reach the new server (timeout). They're reaching the old IP 203.0.113.45 which is now offline.

```
Old setup:
  example.com    A    203.0.113.45    TTL=86400
  
You updated to:
  example.com    A    203.0.113.46    TTL=86400

But 203.0.113.45 is now offline
Users with cached entries can't reach anything
```

Questions:

1. What should you have done before changing the IP?
2. Why are some users reaching the old IP?
3. How long until all users see the new IP?
4. What's the correct sequence for zero-downtime migration?
5. What configuration prevented this issue?

---

**Next**: [Module 8: SSL/TLS Certificates](08-ssl-tls-certificates.md)
