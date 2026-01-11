.PHONY: build run clean test install help

# Build configuration
BINARY_NAME=parking-ingestor
BUILD_DIR=build
GO=go
INSTALL_PATH=/usr/local/bin
CMD_PATH=./cmd/parking-ingestor

# Default target
all: build

# Build the application
build:
	@echo "Building $(BINARY_NAME)..."
	@mkdir -p $(BUILD_DIR)
	$(GO) build -o $(BUILD_DIR)/$(BINARY_NAME) $(CMD_PATH)
	@echo "Build complete!"

# Clean build artifacts and database
clean:
	@echo "Cleaning..."
	rm -rf $(BUILD_DIR)
	rm -f *.db *.db-journal *.db-shm *.db-wal
	@echo "Clean complete!"

# Run tests
test:
	@echo "Running tests..."
	$(GO) test -v ./...

# Install dependencies
deps:
	@echo "Downloading dependencies..."
	$(GO) mod download
	$(GO) mod tidy

# Install binary to system
install: build
	@echo "Installing $(BINARY_NAME) to $(INSTALL_PATH)..."
	sudo cp $(BUILD_DIR)/$(BINARY_NAME) $(INSTALL_PATH)/
	sudo chmod +x $(INSTALL_PATH)/$(BINARY_NAME)
	@echo "Installation complete!"

# Uninstall binary from system
uninstall:
	@echo "Uninstalling $(BINARY_NAME)..."
	sudo rm -f $(INSTALL_PATH)/$(BINARY_NAME)
	@echo "Uninstall complete!"


# Show help
help:
	@echo "Available targets:"
	@echo "  build     - Build the application"
	@echo "  clean     - Remove build artifacts and database files"
	@echo "  test      - Run tests"
	@echo "  deps      - Download and organize dependencies"
	@echo "  install   - Install binary to $(INSTALL_PATH)"
	@echo "  uninstall - Remove binary from $(INSTALL_PATH)"
	@echo "  help      - Show this help message"
