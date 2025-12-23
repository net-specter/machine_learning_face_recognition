# Agile Task Tracker Microservices Project

This repository contains the full stack implementation of an Agile Task Tracker (a simplified Trello/Jira clone) built using **Next.js** for the frontend and **three independent Express.js microservices** for the backend, orchestrated entirely with **Docker Compose**.

## 🚀 Project Overview

This project demonstrates a robust microservices architecture using the **"Database per Service"** pattern. All services communicate via synchronous REST APIs.

### Architecture (Microservices)

The application is split into four main services, each running in its own container and connected to its own isolated MySQL database:

| Service           | Technology | Internal Port | Responsibilities                                                                        | Database           |
| :---------------- | :--------- | :------------ | :-------------------------------------------------------------------------------------- | :----------------- |
| **Auth Service**  | Express.js | `8001`        | User registration, login, JWT issuance, user data validation.                           | `auth-db` (MySQL)  |
| **Board Service** | Express.js | `8002`        | Management of high-level projects, boards, and columns.                                 | `board-db` (MySQL) |
| **Task Service**  | Express.js | `8003`        | Core logic: Task creation, updating task status, comments. **Acts as the API Gateway.** | `task-db` (MySQL)  |
| **Frontend**      | Next.js    | `3000`        | User Interface (Kanban Board).                                                          | N/A                |

### Communication Flow Example

The system relies on internal service-to-service calls:

- When a task is created, the **Task Service** calls the **Auth Service** to verify the user's ID and the **Board Service** to ensure the board exists.
- The **Frontend** only interacts with the public **Task Service** API (exposed at `localhost:3001`).

---

## 🛠️ Prerequisites

- **Docker Desktop:** Required to run the containers.
- **Node.js & NPM/Yarn:** Required locally for initial dependency installation and running Next.js/Express scripts before containerization.

## 📦 Setup and Installation

### 1. Initial Setup (Local)

Before building the Docker images, you must install the dependencies for each Node.js project.

```bash
# Navigate to the root directory of the project

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies for all three services
cd ../backend/auth-service
npm install

cd ../board-service
npm install

cd ../task-service
npm install

# Return to the project root
cd ../../
```

### 2. Configure Environment and Secrets

**IMPORTANT:** The `docker-compose.yml` file contains placeholder Base64 encoded passwords for the MySQL services and a placeholder `JWT_SECRET`. You must update these.

1.  **Update Passwords:** Change all instances of the Base64 strings (e.g., `c2VjdXJlX2F1dGhfcGFzcw==`) and the plaintext `MYSQL_ROOT_PASSWORD`s to your own secure values.
2.  **Update JWT Secret:** Change `"your_super_secret_key"` in the `auth-service` environment block.

### 3. Build and Run Containers

Use Docker Compose to build the images (using the multi-stage Dockerfiles) and start all 7 services:

```bash
# The --build flag forces Docker to build the image using the Dockerfiles
docker compose up --build
```

The first build will take several minutes as it downloads base images and installs dependencies. Subsequent runs will be much faster due to caching.

### 4. Run Sequelize Migrations

Once the database containers (`auth-db`, `board-db`, `task-db`) are running and healthy, you must run the initial schema migrations for each service.

**Run Migrations:**

The following commands execute the migrations inside the respective service containers:

```bash
# Migration for Auth Service
docker exec express-auth-service npx sequelize-cli db:migrate

# Migration for Board Service
docker exec express-board-service npx sequelize-cli db:migrate

# Migration for Task Service
docker exec express-task-service npx sequelize-cli db:migrate
```

Your databases are now initialized and ready for use.

---

## 💻 Usage and Endpoints

| Component              | Access URL              | Exposed Port | Notes                                          |
| :--------------------- | :---------------------- | :----------- | :--------------------------------------------- |
| **Frontend UI**        | `http://localhost:3000` | `3000`       | The main task tracker application.             |
| **Public API Gateway** | `http://localhost:3001` | `3001`       | The Task Service, which the frontend talks to. |

### Backend API Access (Internal/Testing)

You can hit the internal services directly using tools like Postman for testing:

- **Auth Service:** `http://localhost:3001/auth/...` (Handled through the Task Service proxy)
- **Board Service:** `http://localhost:3001/boards/...` (Handled through the Task Service proxy)

---

## 🛑 Teardown

To stop the services and remove the containers and network:

```bash
docker compose down
```

To stop the services and remove the containers, networks, **AND the persistent database volumes**:

```bash
docker compose down -v
```

_(Use this command if you want a completely fresh database state on the next run.)_

## ☁️ DevOps and Production Notes

This setup provides a foundation for a robust deployment pipeline:

- **CI Pipeline:** GitHub Actions would typically run tests, followed by `docker build` (leveraging the multi-stage caching) for the 4 service images.
- **Image Registry:** Built images would be pushed to Docker Hub or AWS ECR.
- **CD Deployment:** Services would be deployed to a container orchestration platform (like AWS ECS Fargate or Kubernetes).
- **Security:** In a production environment, the passwords currently stored in the `docker-compose.yml` file would be loaded securely via **Docker Secrets** or a dedicated Secret Manager service.
