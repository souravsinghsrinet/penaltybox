# PenaltyBox Web Application – Technical Document

## 1. System Architecture
- **Frontend:** React.js (SPA, API-driven, responsive UI).
- **Backend:** FastAPI (REST APIs, JWT-based authentication).
- **Database:** PostgreSQL (via SQLAlchemy + Alembic for migrations).
- **ORM:** SQLAlchemy (with Pydantic models for validation).
- **Hosting:**
  - Backend → Render / Railway / AWS EC2 (to be decided).
  - Frontend → Vercel / Netlify.
  - Database → Supabase / RDS / Railway PostgreSQL.

---

## 2. Core Entities
- **User**
  - `id`, `name`, `email`, `group_id`, `balance`, `created_at`
- **Group**
  - `id`, `name`, `created_at`
- **Penalty**
  - `id`, `user_id`, `group_id`, `amount`, `reason`, `created_at`
- **Proof**
  - `id`, `penalty_id`, `image_url`, `created_at`
- **Payment**
  - `id`, `user_id`, `amount`, `created_at`

---

## 3. Pages & Flows

### (A) Home Page (`/`)
**UI:**
- Welcome message.
- Login / Register buttons.

**Backend API:**
- `POST /auth/register` → create a new account.
- `POST /auth/login` → returns JWT token.

---

### (B) Groups Page (`/groups`)
**UI:**
- List of groups with links.
- Button → "Create New Group".

**Backend API:**
- `GET /groups` → fetch all groups.
- `POST /groups` → create a new group.

---

### (C) Group Detail Page (`/groups/:id`)
**UI:**
- Group name + members.
- List of penalties per user.
- Button → "Add Penalty".

**Backend API:**
- `GET /groups/{id}` → fetch group details.
- `POST /groups/{id}/penalties` → add penalty.

---

### (D) Proofs Page (`/proofs`)
**UI:**
- List of uploaded proofs (images/files).
- Upload form for new proof.

**Backend API:**
- `GET /proofs?penalty_id=x` → fetch proofs for a penalty.
- `POST /proofs` → upload proof (store file + DB entry).

---

### (E) Leaderboard Page (`/leaderboard`)
**UI:**
- Ranking of users by total penalties.

**Backend API:**
- `GET /leaderboard` → aggregate penalties per user.

---

### (F) Payments Page (`/payments`)
**UI:**
- User’s payment history.
- "Pay Dues" button.

**Backend API:**
- `GET /payments/{user_id}` → fetch user’s payments.
- `POST /payments` → add new payment record.

---

## 4. Authentication & Authorization
- JWT-based authentication.
- Endpoints requiring auth: all except `/auth/register` and `/auth/login`.
- Roles: Initially only "User". Later extension: "Admin of Group".

---

## 5. Error Handling
- Consistent JSON error responses.

**Example:**
```json
{ "detail": "Group not found" }