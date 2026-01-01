# Final Project: Production-Ready Observability System

Build a complete, production-grade observability system that integrates all modules. This is a capstone project demonstrating mastery of the curriculum.

## Project Scope

**Timeline**: 20-30 hours  
**Complexity**: Advanced  
**Team**: 1-3 people recommended  

## Requirements Overview

You must deliver:

1. **Infrastructure** (Docker Compose or Kubernetes)
2. **Metrics Collection** (Prometheus)
3. **Log Aggregation** (Loki + Fluent Bit)
4. **Visualization** (Grafana)
5. **Cloud Integration** (AWS CloudWatch)
6. **Alerting** (Rules + Notifications)
7. **Documentation** (Architecture + Operations)
8. **Monitoring of Monitoring** (Meta-observability)

## Detailed Requirements

### 1. Sample Application

Deploy a realistic microservices application with:

- **Frontend Service** (simple web UI)
  - Handles user requests
  - Calls backend APIs
  - Instruments with metrics and logs

- **API Service** (backend REST API)
  - Handles business logic
  - Queries database
  - Makes external API calls
  - Implements structured logging

- **Cache Service** (Redis)
  - Cache layer
  - Hit/miss tracking

- **Database** (PostgreSQL or MySQL)
  - Persistent data
  - Query logging

- **Worker Service** (background jobs)
  - Processes jobs from queue
  - Logs job completion/failure

**Must be real code**, not mock endpoints. Examples:
- Product catalog API
- User management service
- Order processing system
- Analytics pipeline

### 2. Metrics Collection (Prometheus)

**Requirements**:

a) **Application Instrumentation**
   - Counter: Total requests by endpoint/status
   - Gauge: Active requests per endpoint
   - Histogram: Request latency distribution
   - Gauge: Database connections active
   - Counter: Cache hits/misses
   - Histogram: Database query latency

b) **Infrastructure Metrics**
   - CPU usage per service
   - Memory usage per service
   - Disk usage (application data)
   - Network I/O

c) **Prometheus Configuration**
   - Service discovery
   - Scrape intervals (appropriate per metric)
   - Record rules (pre-compute expensive queries)
   - Retention policy (30 days minimum)

d) **Queries (PromQL)**
   - Request rate per service
   - Error rate by endpoint
   - P95 latency
   - Resource utilization
   - Cache hit rate
   - Database connection pool status

### 3. Logging (Structured + Aggregation)

**Requirements**:

a) **Structured Logging**
   - JSON format in all services
   - Standard fields: timestamp, level, service, request_id, message
   - Business-relevant fields (user_id, product_id, etc)
   - No PII in logs (redact before logging)

b) **Log Collection**
   - Fluent Bit configuration
   - Docker integration (read container logs)
   - Kubernetes integration (if using K8s)
   - Log forwarding to Loki

c) **Loki Configuration**
   - Schema configuration
   - Retention policy (30 days minimum)
   - Label strategy (document reasoning)
   - Storage backend (filesystem or S3)

d) **Log Queries (LogQL)**
   - Error logs by service
   - Slow requests (from logs)
   - User activity tracking
   - Service dependency logs

### 4. Visualization (Grafana)

**Requirements**:

a) **Dashboards** (at least 5)
   - **System Overview**: Golden signals for all services
   - **API Service**: Request metrics, latency, errors
   - **Database**: Connections, query performance, replication lag
   - **Infrastructure**: CPU, memory, disk, network
   - **Business Metrics**: User signups, order rate, conversion (from logs)

b) **Dashboard Features**
   - Variables for service/environment filtering
   - Appropriate panel types (timeseries, gauge, table, logs)
   - Clear titles and descriptions
   - Links between related dashboards

c) **Alert Rules** (at least 8)
   - High error rate (service unavailability)
   - High latency (degradation)
   - Service down (up==0)
   - Resource constraints (CPU > 80%, Memory > 85%)
   - Database issues (slow queries, connection pool high)
   - Alert thresholds must be reasonable (not too tight)

d) **Alert Configuration**
   - Notification channels (Slack or email minimum)
   - Appropriate severity levels
   - Meaningful descriptions
   - Links to runbooks

### 5. Cloud Integration (AWS CloudWatch)

**Requirements**:

a) **CloudWatch Metrics**
   - Send custom application metrics to CloudWatch
   - CloudWatch Agent on infrastructure (if using EC2)
   - Integration with Prometheus metrics

b) **CloudWatch Logs**
   - Send application logs to CloudWatch Logs
   - Configure retention policies
   - Create log groups for each service

c) **CloudWatch Alarms**
   - Replicate critical alerts in CloudWatch
   - SNS notifications
   - Lambda for custom actions (optional but impressive)

d) **CloudWatch Dashboards**
   - Unified view of AWS resources
   - Correlation with application metrics

### 6. Security and Access Control

**Requirements**:

a) **Secrets Management**
   - API keys, credentials in environment or secrets manager
   - No hardcoded secrets in code
   - Separate credentials per environment

b) **Access Control**
   - Grafana users with appropriate roles
   - Documentation of who can access what
   - Log access audit trail

c) **Data Protection**
   - No PII in logs or metrics
   - Encryption in transit (HTTPS for APIs)
   - Document retention and deletion policies

### 7. Documentation

**Requirements**:

a) **Architecture Documentation**
   - System diagram
   - Data flow diagram
   - Component descriptions
   - Decisions and tradeoffs

b) **Deployment Guide**
   - Prerequisites
   - Step-by-step setup
   - Configuration explanation
   - Troubleshooting common issues

c) **Operations Manual**
   - Key metrics to monitor
   - Common alerts and responses
   - Scaling procedures
   - Disaster recovery

d) **Runbooks** (at least 5)
   - High error rate
   - Service unavailable
   - Database issues
   - Resource exhaustion
   - Observability system failure

### 8. Monitoring the Monitoring

**Requirements**:

a) **Prometheus Monitoring**
   - Alert on Prometheus target down
   - Monitor TSDB disk usage
   - Track scrape success rate

b) **Loki Monitoring**
   - Alert on ingester lag
   - Monitor disk usage
   - Track log loss (if any)

c) **Grafana Monitoring**
   - Alert if Grafana unreachable
   - Track query errors

d) **Meta-Dashboard**
   - Show health of observability system itself
   - Redundancy checks

## Deliverables Checklist

- [ ] Source code (application + observability config)
- [ ] Docker Compose or Kubernetes manifests
- [ ] Prometheus configuration with record rules
- [ ] Fluent Bit configuration
- [ ] Loki configuration
- [ ] 5+ Grafana dashboards (JSON export)
- [ ] 8+ Alert rules with descriptions
- [ ] Architecture documentation
- [ ] Deployment guide
- [ ] Operations manual
- [ ] 5+ Runbooks
- [ ] README.md with quick start

## Grading Rubric

### Metrics Collection (20%)
- Application properly instrumented (50%)
- Infrastructure metrics collected (25%)
- Queries demonstrate understanding (25%)

### Logging (20%)
- Structured JSON logging throughout (40%)
- Proper log levels used (30%)
- Correlation via request_id demonstrated (30%)

### Visualization (20%)
- Dashboards well-designed and useful (50%)
- Alert rules appropriate and tuned (50%)

### Cloud Integration (10%)
- CloudWatch successfully integrated (70%)
- Demonstrates understanding of cloud-native observability (30%)

### Documentation (15%)
- Architecture clear and complete (40%)
- Deployment guide accurate and thorough (40%)
- Runbooks detailed and actionable (20%)

### Monitoring the Monitoring (10%)
- Observability system health visible (60%)
- Redundancy/failover considered (40%)

### Code Quality & Production Readiness (5%)
- Clean, readable code
- Follows best practices
- Comments where needed
- Error handling appropriate
- Security considered

## Success Criteria

A successful project demonstrates:

1. **End-to-End Understanding**
   - Can explain why each component exists
   - Understands data flow through the system
   - Knows when to alert vs when to log

2. **Practical Skill**
   - Can deploy and configure tools
   - Writes effective queries
   - Designs good dashboards

3. **Production Mindset**
   - Considers cost and scale
   - Plans for failure
   - Documents thoroughly
   - Thinks about operations

4. **System Thinking**
   - Understands relationships between components
   - Sees observability as enabling business
   - Balances tradeoffs (cost vs granularity)

## Example Project Ideas

### Option 1: E-Commerce Platform

```
Services:
- API (user, product, order management)
- Payment processor (external integration)
- Recommendation engine
- Notification service (emails, SMS)
- Admin dashboard

Observability:
- Track order processing from start to finish
- Monitor payment failures
- Alert on recommendation latency
- Dashboard for business metrics (orders/hour, revenue/hour)
```

### Option 2: Real-Time Chat Application

```
Services:
- API (authentication, message storage)
- WebSocket server (real-time messaging)
- Message queue (Kafka or RabbitMQ)
- Search service (Elasticsearch)

Observability:
- Track message latency (user to receiver)
- Monitor queue backlog
- Alert on dropped connections
- Dashboard for user activity
```

### Option 3: Data Pipeline

```
Services:
- Data ingestion (API)
- Stream processor (Kafka)
- Data warehouse (PostgreSQL)
- ML model serving
- Analytics API

Observability:
- Track data freshness
- Monitor processing latency
- Alert on data quality issues
- Dashboard for pipeline health
```

## Tips for Success

### Phase 1: Foundation (Days 1-3)
1. Set up Docker Compose or Kubernetes
2. Deploy Prometheus, Loki, Grafana
3. Deploy sample application
4. Basic instrumentation

### Phase 2: Integration (Days 4-7)
1. Connect metrics and logs
2. Create dashboards
3. Add alerts
4. Implement Fluent Bit

### Phase 3: Polish (Days 8-10)
1. Add CloudWatch integration
2. Tune alert thresholds
3. Create runbooks
4. Document everything

### Phase 4: Verification (Day 11)
1. Test disaster scenarios
2. Verify all alerts work
3. Review documentation
4. Final code review

## Common Mistakes to Avoid

1. **Too complex application**
   - Keep sample app simple (3-5 services max)
   - Focus on observability, not application features

2. **Not enough labels**
   - Design label strategy before implementing
   - Document why each label exists

3. **Boring alerts**
   - Alert on actionable conditions
   - Each alert should have a runbook

4. **Missing documentation**
   - Assume reader knows nothing about your setup
   - Explain every design decision

5. **Overly optimistic thresholds**
   - Alert too early (false positives) or too late (missed issues)
   - Test alerts before finalizing thresholds

## Presentation

If presenting your project:

**5-minute presentation should cover**:
1. What problem does observability solve? (30 sec)
2. System architecture (1 min)
3. Key observability features (2 min)
4. Live demo of alert + response (1 min)

---

**Complete your final project to demonstrate mastery of observability engineering.**
