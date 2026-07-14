```markdown
# DE-Workshop
## Docker - Workshop - CodeSpace

---

## Common Docker Issue — `docker: command not found` Inside a Container

While following the project setup, I encountered an issue where the `docker run` command was not working.

### Error

```bash
root@container:/# docker run -it python:3.13.11

bash: docker: command not found
```

### Root Cause

I was already inside a Docker container.

The terminal prompt:

```bash
root@container:/#
```

indicates that the shell is running inside a container, not on the host machine.

Containers usually do not have Docker installed inside them, so running Docker commands from there results in:

```bash
docker: command not found
```

### Solution

Exit the container first:

```bash
exit
```

Then run the Docker command from the host terminal:

```bash
docker run -it python:3.13.11
```

### Important Concept

Docker commands should normally be executed from the host machine, not from inside a container.

Architecture:

```text
Host Machine
    ↓
Docker Engine
    ↓
Containers
```

I was accidentally trying to run Docker inside a container (Docker-in-Docker scenario), which is an advanced setup and not part of the normal beginner workflow.

### How to Recognize the Difference

#### Inside a Container

```bash
root@container:/#
```

#### On Host Machine

```bash
user@localhost:~$
```

or

```powershell
PS C:\>
```

---

## Troubleshooting: PostgreSQL Port Conflict with Docker

While running the PostgreSQL Docker container, the following issue occurred:

```bash
Bind for 0.0.0.0:5432 failed: port is already allocated
```

### Cause

The local PostgreSQL service on the host machine was already using port `5432`.

Docker containers are isolated, but when using port mapping like:

```bash
-p 5432:5432
```

Docker tries to expose the container through the host machine's port `5432`. Since only one process can use a port at a time, Docker could not start the container.

### Solution 1 — Stop Local PostgreSQL Service

Stop the PostgreSQL service running on the host machine, then restart the container.

Example (Windows Services):

* Open `services.msc`
* Find `postgresql`
* Stop the service

After stopping the service, Docker can successfully bind to port `5432`.

### Solution 2 — Use a Different Host Port

Instead of stopping the local PostgreSQL service, map the container to another host port.

Example:

```bash
docker run -p 5433:5432 postgres
```

This means:

```text
localhost:5433 -> Docker PostgreSQL container
localhost:5432 -> Local PostgreSQL service
```

Now both PostgreSQL instances can run simultaneously without conflicts.

### Important Note

The PostgreSQL service inside the container still runs on port `5432`. Only the host-side exposed port changes. Docker port mapping format:

```text
HOST_PORT:CONTAINER_PORT
```

---

## NYC Yellow Taxi Data Ingestion Script

This Python script downloads **NYC Yellow Taxi trip data** from the public TLC repository and loads it into a PostgreSQL database.  
It is designed to handle the large file sizes (the January 2021 file is ~1.1 GB compressed) by processing the CSV in **chunks** and inserting them efficiently.

### 🧰 Features

- **Command‑line interface** – built with `click`, all parameters are configurable.
- **Chunked reading** – prevents memory overload, uses `pandas.read_csv(iterator=True)`.
- **Explicit schema definition** – sets nullable integer types (`Int64`) and date columns.
- **Progress feedback** – uses `tqdm` to show insertion progress.
- **Safe table creation** – first chunk creates/replaces the table, subsequent chunks append.
- **Connection validation** – tests the PostgreSQL connection before attempting any data load.
- **Input validation** – month parameter is restricted to 1–12.

### 📦 Requirements

- Python 3.9+
- PostgreSQL running (local or Docker)
- Python packages: `click`, `pandas`, `sqlalchemy`, `psycopg[binary]`, `tqdm`

Install with `uv` (or `pip`):

```bash
uv add click pandas sqlalchemy "psycopg[binary]" tqdm
```

### 🚀 Usage

Basic example (defaults: user `root`, password `root`, database `ny_taxi`, year 2021, month 1, table `yellow_taxi_data`):

```bash
python ingest_taxi_data.py
```

Full example with custom parameters:

```bash
python ingest_taxi_data.py \
  --pg-user=myuser \
  --pg-pass=mypass \
  --pg-host=localhost \
  --pg-port=5432 \
  --pg-db=ny_taxi \
  --year=2020 \
  --month=10 \
  --target-table=yellow_taxi_2020_10 \
  --chunksize=50000
```

#### Available options

| Option | Default | Description |
|--------|---------|-------------|
| `--pg-user` | `root` | PostgreSQL user |
| `--pg-pass` | `root` | PostgreSQL password |
| `--pg-host` | `localhost` | PostgreSQL host |
| `--pg-port` | `5432` | PostgreSQL port |
| `--pg-db` | `ny_taxi` | Database name |
| `--year` | `2021` | Year (YYYY) |
| `--month` | `1` | Month (1‑12, validated) |
| `--target-table` | `yellow_taxi_data` | Destination table name |
| `--chunksize` | `100000` | Rows per chunk |
| `--base-url` | (see code) | Alternative data source URL |

### ⚙️ How It Works (Technical Overview)

1. **URL construction** – builds the GitHub release URL for the requested year/month (e.g. `yellow_tripdata_2021-01.csv.gz`).
2. **Database connection** – uses SQLAlchemy with a `postgresql+psycopg://` URL.  
   A test query (`SELECT 1`) validates the connection; fails fast on errors.
3. **Chunked CSV reader** – `pd.read_csv(..., iterator=True, chunksize=N)` returns an iterator.
4. **First chunk** – creates the table with `if_exists='replace'` (drops any old table).  
   The full schema is inferred from the first chunk’s data types (using the explicit `dtype` mapping).
5. **Remaining chunks** – each chunk is appended using `if_exists='append'`.
6. **Progress bar** – `tqdm` shows the number of chunks processed.  
   Total row count is displayed after completion.

### 🔧 Design Decisions (Why We Did It This Way)

- **Explicit `dtype` and `parse_dates`** – ensures correct column types and faster parsing; avoids automatic inference errors.
- **`compression='gzip'`** – required for some systems where pandas does not auto‑detect the compression from the URL.
- **`text("SELECT 1")`** – SQLAlchemy 2.0+ requires raw SQL strings to be wrapped with `text()`.
- **No `method='multi'`** – for simplicity and to avoid hitting PostgreSQL’s parameter limit (65k). If you need faster inserts, reduce `chunksize` and add a `--multi` flag.
- **Click’s `IntRange` validator** – prevents invalid month values without additional if‑statements.
- **Logging vs. `click.echo`** – `click.echo` is sufficient for a CLI tool; logging adds complexity without immediate benefit.

### 🐘 Running the Script with Docker Compose

If you followed the DataTalksClub course, you can run PostgreSQL in Docker:

```bash
docker run -d --name ny_taxi_postgres \
  -e POSTGRES_USER=root \
  -e POSTGRES_PASSWORD=root \
  -e POSTGRES_DB=ny_taxi \
  -p 5432:5432 \
  -v ny_taxi_postgres_data:/var/lib/postgresql/data \
  postgres:16
```

Then execute the script as shown above.

### 📝 Notes

- The script **replaces** the entire table each time it runs. To keep historical data, change `if_exists='replace'` to `'append'` in the first chunk.
- If the script is interrupted (e.g., network failure), it will **not** automatically roll back partial inserts. For production, consider using a staging table or transactions.
- The default data source (GitHub releases) is stable and used by the DataTalksClub course.

---
