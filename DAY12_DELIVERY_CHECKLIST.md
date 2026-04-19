# Delivery Checklist — Day 12 Lab Submission

> **Student Name:** Lã Thị Linh  
> **Student ID:** 2A202600089  
> **Date:** 20/04/2026  
> **GitHub Repository:** `https://github.com/lalinhkhmt-star/Lab12_LaThiLinh_2A202600089.git`

---

## Current Status

| Area | Status | Evidence |
|------|--------|----------|
| Mission answers | Completed | [MISSION_ANSWERS.md](MISSION_ANSWERS.md) |
| Final production agent | Completed locally | [06-lab-complete](06-lab-complete/README.md) |
| Docker build and local stack | Completed | Image size `279MB`, local stack ran with `3` agent replicas |
| Security and reliability checks | Completed locally | `401`, `200`, `429`, `402`, Redis-backed history |
| Screenshots | Completed for local verification | [screenshots](screenshots/README.md) |
| Public cloud URL | Pending | Railway/Render/Cloud Run not deployed yet |
| GitHub visibility review | Pending verify | Remote exists, public access not confirmed in this checklist |

---

## Submission Files

- [x] [MISSION_ANSWERS.md](MISSION_ANSWERS.md) completed
- [x] [DEPLOYMENT.md](DEPLOYMENT.md) created
- [x] Final source code in [06-lab-complete/app](06-lab-complete/app/main.py)
- [x] [06-lab-complete/Dockerfile](06-lab-complete/Dockerfile) is multi-stage
- [x] [06-lab-complete/docker-compose.yml](06-lab-complete/docker-compose.yml) defines full stack
- [x] [06-lab-complete/.env.example](06-lab-complete/.env.example) exists
- [x] [06-lab-complete/.dockerignore](06-lab-complete/.dockerignore) exists
- [x] [06-lab-complete/railway.toml](06-lab-complete/railway.toml) and [06-lab-complete/render.yaml](06-lab-complete/render.yaml) prepared
- [x] [screenshots/dashboard.png](screenshots/dashboard.png), [screenshots/running.png](screenshots/running.png), [screenshots/test.png](screenshots/test.png) created
- [ ] Actual public deployment URL added to `DEPLOYMENT.md`

---

## Requirement Audit

- [x] All code runs without errors in local verification
- [x] Multi-stage Dockerfile
- [x] Docker image under `500MB`
- [x] API key authentication
- [x] Rate limiting `10 req/min`
- [x] Cost guard `$10/month`
- [x] Health check endpoint
- [x] Readiness check endpoint
- [x] Graceful shutdown
- [x] Stateless design with Redis
- [x] Structured JSON logging
- [x] No hardcoded secrets in code
- [x] Production readiness validator passed `20/20`
- [ ] Public URL deployed and accessible from cloud

---

## Pre-Submission Checklist

- [ ] Repository is public or instructor has access
- [x] `MISSION_ANSWERS.md` completed with exercise answers
- [ ] `DEPLOYMENT.md` has working public URL
- [x] All source code is present in `06-lab-complete/app/`
- [x] `README.md` has setup instructions
- [x] No `.env` file is tracked by Git
- [x] No hardcoded secrets in code
- [ ] Public URL is accessible and working
- [x] Screenshots included in `screenshots/`
- [ ] Repository has clear commit history

Notes:
- Local file `06-lab-complete/.env` exists for Docker testing, but `.gitignore` excludes `.env`.
- Git remote is configured to GitHub, but this checklist does not confirm whether the repo is public.
- Current local log shows only one visible commit, so commit history should be reviewed before submitting.

---

## Self-Test Results

| Test | Result |
|------|--------|
| `GET /health` | `200 OK` |
| `GET /ready` | `200 OK` |
| `POST /ask` without API key | `401 Unauthorized` |
| `POST /ask` with valid API key | `200 OK` |
| Rate limit exceeded | `429 Too Many Requests` |
| Budget guard with very low budget | `402 Payment Required` |
| Load balancing through Nginx | Requests observed across `3` instance IDs |
| Stateless behavior | History persisted after removing one agent replica |
| Production readiness script | `20/20` checks passed |
| Docker image size | `279MB` |

---

## Evidence Links

- Mission answers: [MISSION_ANSWERS.md](MISSION_ANSWERS.md)
- Deployment notes: [DEPLOYMENT.md](DEPLOYMENT.md)
- Final project README: [06-lab-complete/README.md](06-lab-complete/README.md)
- Main application: [06-lab-complete/app/main.py](06-lab-complete/app/main.py)
- Docker stack: [06-lab-complete/docker-compose.yml](06-lab-complete/docker-compose.yml)
- Production validator: [06-lab-complete/check_production_ready.py](06-lab-complete/check_production_ready.py)
- Screenshot index: [screenshots/README.md](screenshots/README.md)

---

## Remaining Actions Before Submission

1. Commit current changes and push them to GitHub.
2. Verify the GitHub repository is public or instructor-accessible.
3. Deploy the service to Railway or Render.
4. Update [DEPLOYMENT.md](DEPLOYMENT.md) with the real public URL and real cloud test commands.
5. Re-run the self-test against the public URL.
6. If required by instructor, add a real cloud dashboard screenshot in addition to the local verification screenshots.

---

## Suggested Final Submission Line

```text
GitHub repo: https://github.com/lalinhkhmt-star/Lab12_LaThiLinh_2A202600089.git
```

Current blocker: public deployment URL is not available yet.
