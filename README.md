# Cinema Management System

> **Status:** On-going Development 

This is a high-concurrency Cinema Booking API built with **Django** and **DRF**, utilizing a **Domain-Driven Design (DDD)** to ensure modularity and scalability. The system integrates **Redis** for real-time seat locking, **Stripe** for secure payments, and **JWT** for stateless authentication. 

Designed for production-grade reliability, it features a fully **Dockerized** stack, automated **CI/CD** pipelines via GitHub Actions, and a layered **RBAC** permission system to protect data integrity across all four core domains.

---

## There are 4 different Apps on this project:


### App 1: Screening Domain (Core Logic)
The "engine" of the system, handling theater logistics and scheduling with high data integrity.

#### Key Features:
* **Service Layer Architecture:** Business logic is decoupled from views, ensuring high maintainability and testability.
* **Automated Seat Mapping:** Uses a custom coordinate algorithm to generate a full grid of seats (e.g., A1, A2, B1...) automatically when a Hall is created.
* **Efficient Bulk Operations:** Uses `bulk_create` to insert hundreds of seats in a single database command, ensuring high performance.
* **Atomic Grid Resizing:** If a Hall's size changes, the system handles the mass deletion and re-generation of seats within a transaction.atomic block to prevent data corruption.
* **Advanced Conflict Detection:** 
    * **Auto-Buffer Logic:** Automatically calculates showtime end times by adding a 30-minute cleaning buffer to the movie duration.
    * **Overlap Prevention:** Advanced query logic prevents two movies from being booked in the same hall at the same time.
    * **Proactive Suggestions:** When a hall is busy, the system doesn't just error out—it queries the building and suggests a list of alternative available halls for that time slot.

---

### App 2: Booking Domain (Transaction Logic)
A high-concurrency booking engine that manages ticket sales, seat availability, and temporary reservations using an "Atomic" design.

#### Key Features:
* **Redis-Powered Seat Locking:** Implements a **Temporary Hold system** (10-minute timeout) using Redis to prevent "race conditions" where two users try to buy the same seat at once.
* **Atomic Transaction Management:** Uses `transaction.atomic()` to ensure that Booking creation and Seat linking happen as a single unit—if one fails, the database rolls back to stay clean.
* **Booking Lifecycle Management:**
    * **Pending to Confirmed:** A secure "Waiting Room" flow that moves reservations (booking in Redis) into the permanent Ticket table only after successful payment verification.
    * **Auto-Expiration:** Automatically invalidates bookings if the 10-minute Redis lock expires before payment.
* **Strict Availability Enforcement:** 
    * **Anti-Duplicate Logic**: Prevents a user from creating multiple pending bookings for the same seats.
    * **Sold-Out Protection**: Cross-references the Ticket table before every transaction to ensure seats aren't already permanently sold.

---

### App 3: Payment Domain (Financial Integration)
A secure financial gateway that bridges the cinema's booking logic with the **Stripe API**, ensuring no ticket is issued without a verified transaction.

#### Key Features:
* **Gateway Integration (Stripe):** Uses the Stripe API to securely process credit cards without storing sensitive data on local database.
* **Transaction Lifecycle:** Manages the flow from `INITIALIZED` → `SUCCESS` or `FAILED`.
* **Intelligent Error Handling:** Catches `StripeError` exceptions gracefully, providing clear feedback to the user while logging the failure in the database for troubleshooting.
* **Service-Level Coordination:** Instead of just "Signals," the Payment Service directly coordinates with the `BookingService` to confirm seats only after the bank confirms the funds.
* **Immutable Audit Trail:** Creates a permanent history of `Transaction IDs`, `Amounts`, and `Currency` for financial reporting and future refund processing.

---

### App 4: Identity Domain (Security & Auth)
A secure authentication system using **JWT (JSON Web Tokens)** that manages user lifecycles and strictly enforces field-level permissions.

#### Key Features:
* **JWT Authentication:** Implements industry-standard JSON Web Tokens (SimpleJWT) for secure, stateless authentication.
* **Role-Based Access Control (RBAC):**
    * **Hierarchy Protection:** Prevents lower account from accessing or modifying upper accounts.
    * **Identity Isolation:** Uses custom DRF permissions to ensure users can only view or edit their own private data.
* **Secure Token Blacklisting:** Integrates a logout mechanism that blacklists refresh tokens, ensuring stolen or old sessions cannot be reused.
* **Smart Duplicate Detection:** Uses optimized `Q` objects to check for duplicate emails, usernames, or phone numbers in a single database hit, reducing server load.

---

## Technical Ecosystem & Infrastructure

### Global Security & Permissions Architecture
Security isn't just in the Identity app; it is enforced at the gate of every single endpoint using a **Layered Permission Strategy**:
* **RBAC (Role-Based Access Control):** The system distinguishes between `Customer`, `Staff`, and `Superuser` roles.
* **Owner-Only Access:** Using custom DRF permission classes, the system ensures that a user can only view their own `Booking` history or `Payment` status.
* **Admin Management Suite:** Every domain (Screening, Booking, etc.) includes "Staff-Only" endpoints. These allow admins to:
    * Manually override seat locks in Redis.
    * Force-cancel bookings for maintenance.
    * Generate real-time analytics on ticket sales and hall occupancy.

### DevOps & Deployment Pipeline
This project is built for "Production-First" stability:
* **Fully Dockerized:** The entire environment—Django, PostgreSQL, and Redis—is orchestrated via **Docker Compose**, ensuring "it works on my machine" translates perfectly to the server.
* **Hardened CI/CD (GitHub Actions):** 
    * Every push and pull request triggers an automated test suite.
    * **The "Brute Force" Stability Logic:** The CI pipeline uses a sophisticated wait-mechanic to ensure the PostgreSQL database is fully initialized and healthy before tests run, preventing "unhealthy container" failures.
* **Cloud Orchestration:** Deployed on **Railway**, utilizing internal networking (`.railway.internal`) for high-speed, secure communication between the API, PostgreSQL, and the Redis cache.


---

## Installation & Setup

Before you start, make sure you have the following installed:

### Tech Stack

* **Backend:** Python 3.13, Django, Django Rest Framework (DRF)
* **Database:** PostgreSQL
* **Cache/Lock:** Redis
* **Auth:** JWT (SimpleJWT), Blacklist
* **Payments:** Stripe API
* **Infrastructure:** Docker, GitHub Actions(CI/CD), Railway
* **Server:** Gunicorn & WhiteNoise
* **API Testing:** Postman (for testing protected endpoints via Bearer Tokens)

1. **Clone the repository:**
    ```bash
    git clone https://github.com/alphaRookie/Cinema-management-system-API.git
    ```

2. **Configure Environment Variables**
    Create a `.env` file in the root directory and add your credentials.
    ```env
    DEBUG=True
    SECRET_KEY=your_secret_key
    DB_NAME=cinema_db
    DB_USER=your_name
    DB_PASSWORD=your_password
    DB_HOST=db
    DB_PORT=5432
    REDIS_HOST=redis
    REDIS_PORT=6379
    REDIS_PASSWORD=your_redis_password_here
    STRIPE_PUBLIC_KEY=pk_test_your_key
    STRIPE_SECRET_KEY=sk_test_your_key
    ```

3. **Launch with Docker (Recommended)**
    This single command builds the images, starts the PostgreSQL database, connects the Redis cache, and launches the Django API.
    ```bash
    docker compose up --build
    ```
    *The API will be available at:* `http://127.0.0.1:8000/`

4. Setup the Database & Admin
    In a new terminal window, run the migrations and create your admin account inside the running container:
    ```bash
    # Run Migrations
    docker compose exec web python manage.py migrate

    # Create Admin User
    docker compose exec web python manage.py createsuperuser
    ```

### Manual Setup (Without Docker)
If you prefer to run it natively, ensure you have **PostgreSQL** and **Redis** running on your machine, then:
    1. **Install dependencies:** `pipenv install && pipenv shell`
    2. **Apply migrations:** `python manage.py migrate`
    3. **Start server:** `python manage.py runserver`

---

## Live Testing & Demo Access

> [!WARNING]
> **Service Availability:** This project is hosted on a free/hobbyist tier. If the monthly credit quota is reached, the service may be temporarily hibernated. If the link is unresponsive, please follow the **Docker Setup** below to run it locally.

You can test the API live without setting up a local environment. Use the credentials below to explore different permission levels:

### **Level 1: Customer (Standard User)**
* **Email:** `democustomer321@gmail.com`
* **Password:** `custlog1234567890`
* **Access:** [Login via JWT Endpoint](https://cinema-management-system-api-production.up.railway.app/identity/login) or [Postman]

### **Level 2: Manager (Staff Access)**
* **Email:** `demostaff123@gmail.com`
* **Password:** `stafflog0987654321`
* **Admin Panel:** [https://cinema-management-system-api-production.up.railway.app/admin/](https://cinema-management-system-api-production.up.railway.app/admin/)

> [!NOTE]
> **Permissions:** I already restricted permissions for some actions in these accounts.
