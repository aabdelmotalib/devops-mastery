# Docker: A Professional Container Engineering Curriculum

This is a comprehensive, production-oriented Docker tutorial designed for backend engineers, DevOps engineers, platform engineers, and those preparing for Kubernetes.

## What This Is

- A container engineering curriculum used in real systems
- Not a "Docker for beginners" guide
- Assumes you understand Linux and networking basics
- Focuses on Docker Engine + CLI
- Production patterns from day one

## Container Mental Model

```
Application
    ↓
Process
    ↓
Linux namespaces & cgroups
    ↓
Container runtime
    ↓
Docker Engine
    ↓
Host OS
```

Keep this in mind throughout: containers are isolated processes on a shared kernel, not magic.

## Modules

1. [Container Fundamentals](01-container-fundamentals.md) - What containers actually are
2. [Docker Architecture](02-docker-architecture.md) - Engine, runtime, registry
3. [Docker Images](03-docker-images.md) - Layers, Dockerfile, best practices
4. [Docker Containers](04-docker-containers.md) - Lifecycle, execution, resources
5. [Docker Networking](05-docker-networking.md) - Bridge, host, overlay intro
6. [Docker Volumes & Storage](06-docker-volumes-storage.md) - Persistence strategies
7. [Docker Compose](07-docker-compose.md) - Multi-service orchestration
8. [Docker Security](08-docker-security.md) - Trust, isolation, hardening
9. [Docker in CI/CD](09-docker-cicd.md) - Pipeline integration, tagging
10. [Docker → Kubernetes Readiness](10-docker-kubernetes-readiness.md) - Migration path

## Final Project

[Containerize a Backend Application](final-project.md) - Multi-stage builds, secure execution, data persistence, CI/CD ready.

## How to Use This Tutorial

1. Read each module sequentially
2. Work through the hands-on labs after each module
3. Answer the practice questions to verify understanding
4. Analyze the failure scenarios to build debugging skills
5. Complete the final project to integrate all concepts

## Prerequisites

- Linux familiarity (processes, filesystem, networking)
- Shell scripting basics
- Docker Engine installed (20.10+)
- Docker CLI knowledge basics

## Key Principles

1. Containers are about isolation, reproducibility, and distribution
2. Explain Docker from OS → runtime → application perspective
3. Linux containers only (no desktop containers)
4. Every concept includes real production use cases
5. Trade-offs are always explained
6. Avoid vendor lock-in thinking

## What You'll Learn

- How containers actually work at the OS level
- How to build efficient, secure container images
- Multi-service architecture with Compose
- Networking, storage, and security patterns
- CI/CD integration
- When and how to move to Kubernetes

---

Start with [Module 1: Container Fundamentals](01-container-fundamentals.md)
