# PenaltyBox — API Specifications

> **Auth note:** All endpoints _except_ `/auth/register` and `/auth/login` require authentication via HTTP header:
>
> ```
> Authorization: Bearer <access_token>
> ```

---

## Table of contents
- [Authentication](#authentication)
- [Groups](#groups)
- [Group Details & Penalties](#group-details--penalties)
- [Proofs (payment screenshots)](#proofs-payment-screenshots)
- [Leaderboard](#leaderboard)
- [Payments](#payments)
- [Notifications (future)](#notifications-future)
- [Status codes](#status-codes)

---

## Authentication

### `POST /auth/register`
**Description:** Create a new user account.

**Request** (application/json)
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "mypassword"
}
```

**Response (201 Created)**
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "group_id": null
}
```

---

### `POST /auth/login`
**Description:** Authenticate and receive a JWT access token.

**Request** (application/json)
```json
{
  "email": "john@example.com",
  "password": "mypassword"
}
```

**Response (200 OK)**
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## Groups

### `GET /groups`
**Description:** List all groups.

**Auth:** required

**Response (200 OK)**
```json
[
  { "id": 1, "name": "Hiking Club" },
  { "id": 2, "name": "Football Team" }
]
```

---

### `POST /groups`
**Description:** Create a new group.

**Auth:** required (admin role where applicable)

**Request**
```json
{ "name": "New Group" }
```

**Response (201 Created)**
```json
{ "id": 3, "name": "New Group" }
```

---

### `GET /groups/{id}`
**Description:** Get group details, members, rules, and recent penalties.

**Auth:** required

**Response (200 OK)**
```json
{
  "id": 1,
  "name": "Hiking Club",
  "members": [
    { "id": 1, "name": "Alice", "email": "alice@example.com" },
    { "id": 2, "name": "Bob", "email": "bob@example.com" }
  ],
  "rules": [
    { "id": 11, "title": "Late Arrival", "amount": 200 }
  ],
  "recent_penalties": [
    {
      "id": 5,
      "user_id": 2,
      "amount": 100,
      "reason": "Late arrival",
      "status": "UNPAID",
      "issued_at": "2025-08-15T09:00:00Z"
    }
  ]
}
```

---

## Group Details & Penalties

### `POST /groups/{id}/penalties`
**Description:** Issue a penalty to a member of the group.

**Auth:** required (admin)

**Request**
```json
{
  "user_id": 2,
  "rule_id": 11,
  "amount": 200,
  "note": "Arrived 30 mins late"
}
```

**Response (201 Created)**
```json
{
  "id": 6,
  "user_id": 2,
  "group_id": 1,
  "rule_id": 11,
  "amount": 200,
  "note": "Arrived 30 mins late",
  "status": "UNPAID",
  "issued_at": "2025-09-01T12:00:00Z"
}
```

---

### `GET /users/{user_id}/penalties`
**Description:** Fetch penalties (paid/unpaid) for a user.

**Auth:** required (user or admin)

**Response (200 OK)**
```json
[
  {
    "id": 6,
    "rule": { "id": 11, "title": "Late Arrival" },
    "amount": 200,
    "status": "UNPAID",
    "issued_at": "2025-09-01T12:00:00Z"
  }
]
```

---

## Proofs (payment screenshots)

### `GET /proofs?penalty_id={id}`
**Description:** Get proofs for a specific penalty.

**Auth:** required

**Response (200 OK)**
```json
[
  {
    "id": 1,
    "penalty_id": 6,
    "user_id": 2,
    "image_url": "https://cdn.example.com/proofs/proof1.png",
    "status": "PENDING",
    "created_at": "2025-09-02T10:00:00Z"
  }
]
```

---

### `POST /proofs`
**Description:** Upload a payment proof (multipart/form-data).

**Auth:** required

**Request (multipart/form-data)**  
- `penalty_id` (number)  
- `file` (image/jpeg|png)  
- `note` (optional text)

**Example (curl)**
```bash
curl -X POST "https://api.penaltybox.app/proofs"   -H "Authorization: Bearer <token>"   -F "penalty_id=6"   -F "file=@/path/to/proof.png"   -F "note=Paid via UPI ref 12345"
```

**Response (201 Created)**
```json
{
  "id": 2,
  "penalty_id": 6,
  "user_id": 2,
  "image_url": "https://cdn.example.com/proofs/proof2.png",
  "status": "PENDING",
  "created_at": "2025-09-02T10:05:00Z"
}
```

---

### `POST /proofs/{proof_id}/review`
**Description:** Admin approves or declines a proof.

**Auth:** required (admin)

**Request**
```json
{
  "approve": true,
  "note": "Verified UPI txn id 12345"
}
```

**Response (200 OK)** (approved example)
```json
{
  "id": 2,
  "penalty_id": 6,
  "status": "APPROVED",
  "reviewed_by": 1,
  "reviewed_at": "2025-09-02T11:00:00Z"
}
```

**Side effects:**  
- If approved: penalty status becomes `PAID`, user's total-paid amount updated, notifications sent.  
- If declined: proof status becomes `DECLINED`, penalty remains `UNPAID`, notification sent to user (optional admin note).

---

## Leaderboard

### `GET /leaderboard`
**Description:** Returns users ranked by **total amount paid** (descending). Ranking is based **only** on paid amounts.

**Auth:** required

**Response (200 OK)**
```json
[
  { "user_id": 1, "name": "Aditi Sharma", "total_paid": 5000 },
  { "user_id": 2, "name": "Rohan Verma", "total_paid": 4200 }
]
```

---

## Payments

### `GET /payments/{user_id}`
**Description:** Fetch a user’s payment history.

**Auth:** required (user or admin)

**Response (200 OK)**
```json
[
  { "id": 1, "user_id": 2, "amount": 200, "method": "UPI", "created_at": "2025-09-02T10:00:00Z" }
]
```

---

### `POST /payments`
**Description:** Record a payment without proof (e.g., cash) — admin must approve or mark as received.

**Auth:** required

**Request**
```json
{
  "user_id": 2,
  "amount": 200,
  "method": "CASH",
  "note": "Paid to treasurer"
}
```

**Response (201 Created)**
```json
{
  "id": 3,
  "user_id": 2,
  "amount": 200,
  "status": "PENDING_APPROVAL",
  "created_at": "2025-09-02T10:30:00Z"
}
```

---

## Notifications (future)
- Reminders, approvals and declines sent via Email, SMS, and WhatsApp.
- Suggested approach: background worker / scheduler (Celery, RQ, or FastAPI BackgroundTasks) sends messages based on admin settings and daily cron.

---

## Status codes
- `200 OK` — success (GET/updates)  
- `201 Created` — new resource created  
- `400 Bad Request` — client error (invalid input)  
- `401 Unauthorized` — missing/invalid token  
- `403 Forbidden` — user lacks permission (e.g., non-admin)  
- `404 Not Found` — entity not found  
- `500 Internal Server Error` — unexpected server error
