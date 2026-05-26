# DE-Workshop
Docker - Workshop - CodeSpace
-------------------------

## Common Docker Issue — `docker: command not found` Inside a Container

While following the project setup, I encountered an issue where the `docker run` command was not working.

### Error

```bash
root@container:/# docker run -it python:3.13.11

bash: docker: command not found
```

---

## Root Cause

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

---

## Solution

Exit the container first:

```bash
exit
```

Then run the Docker command from the host terminal:

```bash
docker run -it python:3.13.11
```

---

## Important Concept

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

---

## How to Recognize the Difference

### Inside a Container

```bash
root@container:/#
```

### On Host Machine

```bash
user@localhost:~$
```

or

```powershell
PS C:\>
```
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

Docker tries to expose the container through the host machine's port `5432`.

Since only one process can use a port at a time, Docker could not start the container.

---

## Solution 1 — Stop Local PostgreSQL Service

Stop the PostgreSQL service running on the host machine, then restart the container.

Example (Windows Services):

* Open `services.msc`
* Find `postgresql`
* Stop the service

After stopping the service, Docker can successfully bind to port `5432`.

---

## Solution 2 — Use a Different Host Port

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

---

## Important Note

The PostgreSQL service inside the container still runs on port `5432`.

Only the host-side exposed port changes.

Docker port mapping format:

```text
HOST_PORT:CONTAINER_PORT
```
