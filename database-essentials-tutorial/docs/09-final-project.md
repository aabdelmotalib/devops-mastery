# Final Project: Complete Backend Database Layer

## Project Overview

Build a production-ready backend database layer for a **Task Management API** that demonstrates all concepts from the tutorial.

## Requirements

### Core Features

1. **User Management**
   - User registration and authentication
   - User profiles
   - Email verification

2. **Team Management**
   - Create teams
   - Add/remove team members
   - Team roles (owner, admin, member)

3. **Project Management**
   - Projects belong to teams
   - Project members (subset of team)
   - Project status tracking

4. **Task Management**
   - Tasks belong to projects
   - Task assignments
   - Task status, priority, due dates
   - Task comments
   - Task tags

5. **Activity Logging**
   - Log all important actions
   - Queryable activity feed

### Technical Requirements

1. **PostgreSQL** for core data
   - Users, teams, projects, tasks
   - Proper relationships and constraints
   - Optimized indexes

2. **MongoDB** for flexible data
   - Activity logs
   - Task comments (nested structure)

3. **Redis** for caching and sessions
   - User session storage
   - Cache frequently accessed data
   - Rate limiting

4. **SQLAlchemy ORM**
   - Models with relationships
   - Repository pattern
   - Query optimization

5. **Alembic Migrations**
   - Version-controlled schema
   - Safe migration patterns

6. **Transaction Safety**
   - ACID-compliant operations
   - Proper error handling
   - Optimistic/pessimistic locking where needed

## Database Schema

### PostgreSQL Tables

```sql
-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Teams
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    owner_id INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Team Members
CREATE TABLE team_members (
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('owner', 'admin', 'member')),
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (team_id, user_id)
);

-- Projects
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'completed')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'todo' CHECK (status IN ('todo', 'in_progress', 'done', 'cancelled')),
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assigned_to INTEGER REFERENCES users(id) ON DELETE SET NULL,
    due_date TIMESTAMP,
    created_by INTEGER NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tags
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    color VARCHAR(7) DEFAULT '#000000'
);

-- Task Tags
CREATE TABLE task_tags (
    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_teams_slug ON teams(slug);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
CREATE INDEX idx_projects_team_id ON projects(team_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_assigned_to ON tasks(assigned_to);
CREATE INDEX idx_tasks_status_priority ON tasks(status, priority);
CREATE INDEX idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
```

### MongoDB Collections

```javascript
// Activity logs
{
  "_id": ObjectId("..."),
  "user_id": 123,
  "action": "task_created",
  "resource_type": "task",
  "resource_id": 456,
  "metadata": {
    "task_title": "Implement feature X",
    "project_id": 789
  },
  "timestamp": ISODate("2024-01-01T12:00:00Z")
}

// Task comments
{
  "_id": ObjectId("..."),
  "task_id": 456,
  "user_id": 123,
  "content": "This is a comment",
  "created_at": ISODate("2024-01-01T12:00:00Z"),
  "updated_at": ISODate("2024-01-01T12:00:00Z")
}
```

## Implementation Checklist

### Phase 1: Setup
- [ ] Create project structure
- [ ] Configure PostgreSQL, MongoDB, Redis
- [ ] Set up SQLAlchemy
- [ ] Initialize Alembic
- [ ] Create base models

### Phase 2: Core Models
- [ ] Implement User model
- [ ] Implement Team model
- [ ] Implement Project model
- [ ] Implement Task model
- [ ] Implement Tag model
- [ ] Create relationships

### Phase 3: Repositories
- [ ] UserRepository (CRUD + authentication)
- [ ] TeamRepository (team management)
- [ ] ProjectRepository (project operations)
- [ ] TaskRepository (task operations)
- [ ] ActivityLogRepository (MongoDB)

### Phase 4: Services
- [ ] AuthService (login, registration, sessions)
- [ ] TeamService (team operations with transactions)
- [ ] TaskService (task operations with caching)
- [ ] ActivityService (logging to MongoDB)

### Phase 5: Migrations
- [ ] Initial schema migration
- [ ] Add indexes migration
- [ ] Test rollback

### Phase 6: Caching
- [ ] Cache user profiles
- [ ] Cache team data
- [ ] Cache project lists
- [ ] Implement cache invalidation

### Phase 7: Performance
- [ ] Add appropriate indexes
- [ ] Optimize N+1 queries
- [ ] Implement connection pooling
- [ ] Add query monitoring

### Phase 8: Testing
- [ ] Test CRUD operations
- [ ] Test transactions
- [ ] Test concurrent operations
- [ ] Test cache invalidation
- [ ] Load testing

## Deliverables

1. **Complete codebase** with:
   - All models
   - All repositories
   - All services
   - Migration files

2. **Documentation**:
   - Setup instructions
   - API usage examples
   - Database schema diagram
   - Performance considerations

3. **Tests**:
   - Unit tests for repositories
   - Integration tests for services
   - Transaction tests

4. **Performance report**:
   - Query analysis (EXPLAIN)
   - Index usage
   - Cache hit rates
   - Response times

## Evaluation Criteria

1. **Correctness** (30%)
   - All features work as specified
   - No data integrity issues
   - Proper error handling

2. **Database Design** (25%)
   - Proper normalization
   - Appropriate indexes
   - Correct relationships
   - Constraints enforced

3. **Performance** (20%)
   - Optimized queries
   - Effective caching
   - No N+1 problems
   - Connection pooling

4. **Transaction Safety** (15%)
   - ACID compliance
   - Proper locking
   - Error handling
   - Rollback support

5. **Code Quality** (10%)
   - Clean code
   - Repository pattern
   - Proper separation of concerns
   - Documentation

## Bonus Challenges

1. **Implement soft deletes** for tasks
2. **Add full-text search** for tasks using PostgreSQL
3. **Implement task dependencies** (task A blocks task B)
4. **Add real-time notifications** using Redis pub/sub
5. **Implement audit trail** for all changes
6. **Add database sharding** for horizontal scaling
7. **Implement read replicas** for scaling reads

## Getting Started

```bash
# Clone starter template
cd backend

# Install dependencies
pip install -r requirements.txt

# Setup databases
docker-compose up -d

# Run migrations
alembic upgrade head

# Run tests
pytest

# Start development server
python run.py
```

## Resources

- PostgreSQL documentation
- MongoDB documentation
- Redis documentation
- SQLAlchemy documentation
- Alembic documentation
- Tutorial modules 1-8

## Submission

Submit:
1. Complete source code
2. README with setup instructions
3. Database schema diagram
4. Performance report
5. Test results

Good luck!
