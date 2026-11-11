### City Event Explorer
A Telegram Bot and Web Scraper that aggregates local events from multiple sources, normalizes the data, and allows users to search, filter, and get notified about upcoming events.

This project was created to make it easier to find events for the weekend, as well as events within your favorite genres.

At the moment, only basic functionality has been implemented, namely:
- search by various parameters (genre, type)
- search by dates (weekend, next weekend, this week, custom dates)

In the future, it will also be possible to subscribe to genres and types in order to receive notifications about events.

<p align="center">
  <img src="docs/architecture.png" alt="System Architecture" width="800">
</p>

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed on your machine:
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)
- [Make](https://www.gnu.org/software/make/)
- Python 3.11+
- Dependency manager compatible with `pyproject.toml` [Poetry](https://python-poetry.org/)

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```
### 2. Configure Environment Variables
Copy the example environment file and fill in your details:
```bash
cp .env.example .env
```
.env Configuration:
```Ini
ENV=dev

POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=events_db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/events_db

TG_BOT_TOKEN=your_telegram_bot_token
```

### 3. Database Migrations
Make sure your SQL migration files (0001_... to 0006_...) are mounted to your Postgres container's initialization folder, or run them manually/via your migration tool.

Running the Project
Using Docker
The easiest way to run the entire stack (Database + Bot/Scraper) is using the Makefile and docker-compose.

Start the database:
```bash
docker-compose up -d
```
Install dependencies:
```bash
poetry install
```
Run the application:
```bash
poetry run python src/main.py
```

## 🛠 Makefile Commands Cheat Sheet
We use a Makefile to simplify common operations. Here are the available commands:

Command	Description
* make up - Applies all pending migrations to the database
* make down - Rolls back the latest applied migration.
* make status - Check the status of migrations
* make create - Create a new migration (example: make create name=add_users_table)

