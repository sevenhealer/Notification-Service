# Notification Service
A backend notification system built using **FastAPI**, **PostgreSQL**, and **Celery** with support for sending messages via **Email**, **SMS (mocked)**, and **In-App** channels.
## 🧪 Try It Out
### 🔹 Send a Notification(email)

![Send Notification](Screenshot/1.png)
![Receive Notification](Screenshot/2.png)

**Endpoint:**  
`POST https://noti-api.sevenhealers.in/notifications`

**Try with this JSON:**
```json
{
  "user_id": 1,
  "type": "email",
  "message": "Notification Service Testing with email",
  "recipient_address": "22051604@kiit.ac.in" // ← Replace this with your email to receive the notification
}
```
**📌 Curl Command:**
```bash
curl -X POST https://noti-api.sevenhealers.in/notifications \
-H "Content-Type: application/json" \
-d '{
  "user_id": 1,
  "type": "email",
  "message": "Notification Service Testing with email",
  "recipient_address": "22051604@kiit.ac.in"
}'
```
**✅ Expected Response:**
```json
{
  "id": 55,
  "user_id": 1,
  "type": "email",
  "message": "Notification Service Testing with email",
  "status": "pending",
  "created_at": "2025-05-18T18:07:25.404851Z",
  "updated_at": null,
  "recipient_address": "22051604@kiit.ac.in"
}
```
----------
### 🔹 Send a Notification(sms)

![Send Notifications](Screenshot/3.png)
![Receive Notifications](Screenshot/4.png)

### 🔹 View Notifications for a User

![Get Notifications](Screenshot/5.png)
![Get Notifications](Screenshot/6.png)

**Endpoint:**  
`GET https://noti-api.sevenhealers.in/users/1/notifications`

**📌 Try in your browser:**  (May need to reload)
[https://noti-api.sevenhealers.in/users/1/notifications](https://noti-api.sevenhealers.in/users/1/notifications)

**✅ Expected Response:**

```json
`{  "notifications":  [  {  "id":  55,  "user_id":  1,  "type":  "email",  "message":  "Testing from AWS",  "status":  "sent",  "created_at":  "2025-05-18T18:07:25.404851Z",  "updated_at":  "2025-05-18T18:07:29.196553Z",  "recipient_address":  "22051604@kiit.ac.in"  }  ]  }`
```
## 🔧 Features

-  **API Endpoints*
-  `POST /notifications` - Create and queue a new notification.
-  `GET /users/{user_id}/notifications` - Retrieve all notifications for a user.
-  `GET /notifications/{notification_id}` - Get notification details.
-  `GET /health` - Health check endpoint.

 **Notification Channels**
- Email (mock or SMTP)
- SMS (mocked, placeholder for Twilio)
- In-App (stored in DB)
- 
**Asynchronous Processing**
- Using Celery with Redis as broker/backend.

**Retry Logic**
- Celery-based retry mechanism on failure.

**Database**
- PostgreSQL using SQLAlchemy ORM.

## 🗂️ Project Structure
├── config.py # App settings
├── crud.py # DB operations
├── database.py # DB connection
├── main.py # FastAPI app & routes
├── models.py # SQLAlchemy models
├── schemas.py # Pydantic schemas
├── tasks.py # Celery tasks
├── test.py # Sample tests
├── requirements.txt # Python dependencies
├── .env # Environment variables
└── venv/ # Virtual environment

## ⚙️ Tech Stack
-  **Framework:** FastAPI
-  **Database:** PostgreSQL
-  **Async Tasks:** Celery
-  **Broker:** RabbitMQ
-  **Email:** SMTP via `smtplib` (mockable)
-  **SMS:** Mocked (Twilio-ready)

## 🛠️ Local Setup (Without Docker)
### 1. Clone the Repository
```bash
git  clone  <your-repo-url>
cd  <project-directory>
```
### 2. Create a Virtual Environment
`python -m venv venv source venv/bin/activate # Windows: venv\Scripts\activate`  
### 3. Install Dependencies
`pip install -r requirements.txt`
### 4. Set Environment Variables
Create a `.env` file in the root directory with the following (adjust values as needed):
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/notificationdb
# Celery with RabbitMQ
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
CELERY_RESULT_BACKEND=rpc://
# Email settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your.email@example.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM_ADDRESS=noreply@example.com
USE_TLS=True`
```
### 5. Setup the Database
Ensure PostgreSQL is running, create the database, and then run:
```python
>>>  from database import create_db_tables
>>> create_db_tables()
```
## ▶️ Run the Application

### 1. Start FastAPI
```bash
uvicorn  main:app  --reload`
```
- Access Swagger docs at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Start the Celery Worker

Ensure RabbitMQ is running locally (default at `localhost:5672`) and then run:
```bash
celery  -A  tasks.celery_app  worker  --loglevel=info`
```
## 📬 API Usage
### `POST /notifications`
```bash
{
"user_id":  1,
"message":  "Your OTP is 123456",
"type":  "email",
"recipient_address":  "22051604@kiit.ac.in"
}
```
### `GET /users/{user_id}/notifications`
Fetches all notifications for a user.
### `GET /notifications/{notification_id}`
Fetches a specific notification.