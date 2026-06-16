# Ticketing Platform

### This repository exists both on Gitlab and Github:

- **GitLab**: [https://gitlab.com/arakelyanva/ticketing-platform](https://gitlab.com/arakelyanva/ticketing-platform)
- **Github**: [https://github.com/arakelyanva/ticketing-platform](https://github.com/arakelyanva/ticketing-platform)

## Getting started

To be able to launch the project locally, you will need:

- Python 3.10+
- libuv (since project setup is using `uv`, use `pip install uv`)

### OR

- Docker (version does not really matter, mine is `29.5.1` at the time of making this)

## How to launch the project

- copy `.env.sample` as a `.env` (`cp .env.sample .env`), add some changes if you want, likes of `FASTAPI_PORT` or `DATABASE_URL` (just make sure that the SQLite file will be located in `./db` directory)

### Easier way using Docker

- If you need DB seeds, set `FASTAPI_ENV=test` in your `.env` file first
- After setting up the `.env` file, run `docker compose up -d --build` and wait for it to finish
- Then go to `http://localhost:${FASTAPI_PORT}/docs` To see the API documentation

### Manual launch from the source

- `touch ./db/tickets_db.sqlite` (if its not created already)
- `uv run sync --all-groups`
- `uv run alembic upgrade head`
- `uv run python -m app.seeds.run_seeder` (in case you need seeds for DB)
- `uv run uvicorn --host 127.0.0.1 --port [YOUR_FASTAPI_PORT]` (e.g. YOUR_FASTAPI_PORT=8000)

### Run linter and tests

The project has both Github and GitLab Actions to run CI automatically upon direct push or pull request.

In order to do it locally, you need to run:
- `uv run ruff check` (For linting)
- `uv run pytest --cov=app tests/ --cov-report=term-missing` (For unit and integration tests)

## Brief description of the project and endpoints

The project represents a small fragment of a real world ticketing platform, utilizing these 6 endpoints:
- **GET** `/api/v1/events`
- **POST** `/api/v1/events`
- **GET** `/api/v1/events/{event_id}`
- **POST** `/api/v1/events/{event_id}/book`
- **POST** `/api/v1/bookings/{booking_id}/pay`

#### Brief description of the endpoints
- You can create an event using the **POST** `/api/v1/events` endpoint. You will receive a **201 CREATED** status upon successful creation and all the necessary fields for the event.
- Then, you can book a ticket for the event using the **POST** `/api/v1/events/{event_id}/book` endpoint. You will receive a **201 CREATED** status upon successful booking creation and the `booking_id` for the booking.
- Then, you can pay for the booking using the **POST** `/api/v1/bookings/{booking_id}/pay` endpoint. You will receive a **201 CREATED** status upon successful payment creation, as well as all the necessary fields for the payment.

#### Some specifics for the endpoints
- **POST** `/api/v1/events/{event_id}/book` handles the case when it can be a single available ticket left, but multiple concurrent requests are being done to obtain the ticket, using `asyncio.Lock()`. So the first request which gets processed will receive **201 CREATED** status, and the rest will receive **409 CONFLICT**

- **POST** `/api/v1/bookings/{booking_id}/pay` handles the cases when connection can be lost during the payment transaction, and in case the payment is still in **PENDING** status, the client can continue with it again after restoring connection using the same `Idempotency-Key` header, which was sent during the initial request. In case the payment was **SUCCESS** or **FAILED** during that period of time, using the same `Idempotency-Key` will result in **409 CONFLICT** error, since it was already processed.

