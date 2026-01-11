# Build stage
FROM golang:1.22-alpine AS builder

# Install build dependencies
RUN apk add --no-cache gcc musl-dev sqlite-dev

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY cmd/ cmd/
COPY internal/ internal/

# Build the application
RUN go build -o parking-ingestor ./cmd/parking-ingestor

# Runtime stage
FROM alpine:latest

# Install runtime dependencies
RUN apk add --no-cache ca-certificates sqlite-libs tzdata

# Create non-root user
RUN addgroup -g 1000 parking && \
    adduser -D -u 1000 -G parking parking

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/parking-ingestor .

# Create data directory for database
RUN mkdir -p /data && chown parking:parking /data

# Switch to non-root user
USER parking

# Set data volume
VOLUME /data

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD test -f ${DB_PATH} || exit 1

# Run the application
ENTRYPOINT ["./parking-ingestor"]
CMD ["-db", "/data/parking.db", "-interval", "5m", "-cities", "Karlsruhe,Heidelberg"]
