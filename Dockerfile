FROM python:3.12-slim-bullseye as builder

RUN apt update && apt install -y make

WORKDIR /build

COPY pyproject.toml .
COPY Makefile .
COPY requirements*.txt .
RUN make install-build-lock

COPY trader trader
COPY migrations migrations
COPY alembic.ini .
RUN make migrations
RUN make pex

# run the python executable
FROM python:3.12-slim-bullseye

WORKDIR /app
COPY --from=builder /build/db.db /app/db.db
COPY --from=builder /build/trader.pex /app/trader.pex

ENTRYPOINT ["/app/trader.pex"]
