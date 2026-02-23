# Cinema Management System (Modular Backend) 

> **Status:** On-going Development (Currently finishing App 2; to be continue to App 3 soon)

This is a cinema booking backend built with Django and Django REST Framework. I built this using a Domain-Driven style, which means the code is organized based on its business functions. This makes the project much easier to scale and maintain.

---

## There are 4 different Apps on this project:

## App 1: Screening Domain

**Cinema stage management system.**

* **Automatic seat generation** when creating hall(instead of inserting the seat manually)
* **Prevents overlapping** showtimes in same hall at the same time.
* **Smart suggestions:** If a selected hall is busy, the system suggests available halls during that specific time slot.

---

## App 2: Booking Domain

**Concurrency-safe transaction engine.**

* **Seat lock system** (10-minute reservation window and Prevents double booking)
* **Price freeze** (locking the price at the moment of purchase, future price change won't affect the history)
* **Clear separation:** SeatLock (temporary) vs Ticket (ownership)

---

## App 3: Identity Domain (Soon)

**Unified user & authentication system.**

* **Identity Isolation:** Keeps personal user data and contact info separate from the cinema business logic.
* **Secure Auth:** Handles login, registration, and permission levels (Admin vs Customer).
* **Activity Tracking:** Connects users to their specific booking history via secure Foreign Key relationships

---

## App 4: Transaction Domain (Soon)

**Financial audit & payment gateway.**

* **Payment Isolation:** Dedicated space for money-related logic (refunds, retries, and bank communication).
* **The Handshake:** Uses a "Signal" system to notify the Booking Domain once a payment is successful.
* **Audit Trail:** Maintains a permanent, unchangeable record of every financial transaction for business reporting.

---

## Technical Highlights

* **Atomic Transactions:** When creating a hall and its seats, it’s "all or nothing." If the seat generation fails, the hall isn't created either. No messy half-finished data.
* **Smart Admin:** The Django Admin panel is connected to the Services, so even if an Admin changes something manually, the business rules still apply.
* **Namespaced Routing:** Each domain manages its own URLs, keeping the main config file clean and professional.
* **Service-layer architecture** (no business logic in views)
* **Multi-layer validation** (DB + serializer + service)

---

## Installation & Setup

Before you start, make sure you have the following installed:

#### Here are my tech stack:

* **Python 3.13** 
* **PostgreSQL** 
* **Django**
* **Django REST Framework (DRF)** 


1. **Clone the repository:**
   ```bash
   git clone https://github.com/alphaRookie/Cinema-management-system-API.git
   ```

2. **Setup Environment(optional):**
    ```bash
    pipenv install && pipenv shell
    ```

3. **Migrate and run:**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    python manage.py runserver
    ```

4. **Access the API:**
    Once the server is running, you can explore few endpoints, for example:
    ```bash
    * http://127.0.0.1:8000/screening/...
    * http://127.0.0.1:8000/booking/...
    ```

**Additional: Create Admin Account**
To access the "Smart Admin" panel and manage movies or halls, create a superuser:

```bash
python manage.py createsuperuser

```

*Follow the prompts to set your username, email, and password.*

**Access via:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
