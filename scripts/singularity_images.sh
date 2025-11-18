#!/bin/bash

# This script has separate functions to push Docker images and pull/convert to Singularity SIF files.

set -e

DOCKER_STUB="domain-annotation-pipeline-"
USERNAME=sillitoe
REMOTE=ghcr.io
DOCKER_COMPOSE_FILE=docker-compose.cs.yml
SIF_DIR="./sif_files"

# Function to build and push Docker images to registry
push_docker_images() {
    local specific_service="$1"
    echo "=== PUSHING DOCKER IMAGES ==="
    
    docker login $REMOTE
    
    # Uncomment to build images first
    # echo "Building Docker images..."
    # docker compose -f $DOCKER_COMPOSE_FILE build

    # Get list of services to process
    local services
    if [ -n "$specific_service" ]; then
        services="$specific_service"
        echo "Processing specific service: $specific_service"
    else
        services=$(docker compose -f $DOCKER_COMPOSE_FILE config --services)
        echo "Processing all services"
    fi

    for image_alias in $services; do

        image_name="${DOCKER_STUB}${image_alias}"
        echo "Processing image: ${image_name}"
        
        IMAGE_TAG_NAME="${REMOTE}/${USERNAME}/${image_name}"

        # Tag the image
        echo "Tagging image ${image_name} as ${IMAGE_TAG_NAME}:latest"
        docker tag "${image_name}:latest" "${IMAGE_TAG_NAME}:latest"

        echo "Pushing ${IMAGE_TAG_NAME}:latest"
        docker push ${IMAGE_TAG_NAME}:latest
        echo "✓ Pushed: ${IMAGE_TAG_NAME}:latest"

    done
    
    echo "=== DOCKER PUSH COMPLETE ==="
}

# Function to pull Docker images and convert to Singularity SIF files
pull_singularity_images() {
    local specific_service="$1"
    echo "=== PULLING TO SINGULARITY SIF FILES ==="
    
    # Create directory for SIF files
    mkdir -p "$SIF_DIR"
    
    # Set up Singularity Docker credentials if needed
    if [ -n "$GHCR_TOKEN" ]; then
        export SINGULARITY_DOCKER_USERNAME=${USERNAME}
        export SINGULARITY_DOCKER_PASSWORD=${GHCR_TOKEN}
        echo "Using provided GHCR_TOKEN for authentication"
    else
        echo "Warning: GHCR_TOKEN not set. May need authentication for private repositories."
    fi

    # Get list of services to process
    local services
    if [ -n "$specific_service" ]; then
        services="$specific_service"
        echo "Processing specific service: $specific_service"
    else
        services=$(docker compose -f $DOCKER_COMPOSE_FILE config --services)
        echo "Processing all services"
    fi

    for image_alias in $services; do

        image_name="${DOCKER_STUB}${image_alias}"
        IMAGE_TAG_NAME="${REMOTE}/${USERNAME}/${image_name}"
        SIF_FILE="${SIF_DIR}/${image_name}.sif"
        
        echo "Processing: ${image_alias} -> ${SIF_FILE}"
        
        # Remove existing SIF file if it exists
        if [ -f "$SIF_FILE" ]; then
            echo "Removing existing SIF file: ${SIF_FILE}"
            rm "$SIF_FILE"
        fi
        
        # Pull Docker image and convert to SIF
        echo "Pulling and converting: docker://${IMAGE_TAG_NAME}:latest"
        singularity pull "$SIF_FILE" "docker://${IMAGE_TAG_NAME}:latest"
        
        if [ -f "$SIF_FILE" ]; then
            echo "✓ Created: $(basename $SIF_FILE) ($(du -h $SIF_FILE | cut -f1))"
        else
            echo "✗ Failed to create: $(basename $SIF_FILE)"
        fi

    done
    
    echo ""
    echo "=== SINGULARITY PULL COMPLETE ==="
    echo "SIF files created in: ${SIF_DIR}/"
    ls -lh "$SIF_DIR"/*.sif 2>/dev/null || echo "No SIF files found"
}

# Function to show usage
usage() {
    echo "Usage: $0 [push|pull|both] [service_name]"
    echo ""
    echo "Commands:"
    echo "  push [service]  - Build and push Docker images to registry"
    echo "  pull [service]  - Pull Docker images and convert to Singularity SIF files"
    echo "  both [service]  - Run both push and pull operations"
    echo ""
    echo "Arguments:"
    echo "  service_name    - Optional: specific service to process (e.g., cath-af-cli)"
    echo "                    If omitted, all services will be processed"
    echo ""
    echo "Environment variables:"
    echo "  GHCR_TOKEN - GitHub Container Registry token (required for private repos)"
    echo ""
    echo "Examples:"
    echo "  $0 push                    # Push all Docker images"
    echo "  $0 push cath-af-cli        # Push only cath-af-cli"
    echo "  $0 pull                    # Pull and convert all to SIF"
    echo "  $0 pull cath-af-cli        # Pull and convert only cath-af-cli"
    echo "  GHCR_TOKEN=xxx $0 pull     # Pull with authentication"
    echo "  $0 both                    # Push then pull all"
    echo "  $0 both cath-af-cli        # Push then pull only cath-af-cli"
}

# Main script logic
case "${1:-}" in
    push)
        push_docker_images "$2"
        ;;
    pull)
        pull_singularity_images "$2"
        ;;
    both)
        push_docker_images "$2"
        echo ""
        pull_singularity_images "$2"
        ;;
    *)
        usage
        exit 1
        ;;
esac

echo ""
echo "=== USAGE INSTRUCTIONS ==="
echo "To use SIF files on HPC cluster:"
echo "  singularity exec ${SIF_DIR}/<service>.sif <command>"
echo ""
echo "To copy SIF files to remote server:"
echo "  scp ${SIF_DIR}/*.sif user@server:/path/to/destination/"

