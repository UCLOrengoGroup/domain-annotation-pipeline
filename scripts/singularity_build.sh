#!/bin/bash

# This script tags and pushes a set of Docker images to a Docker registry.

set -e

DOCKER_STUB="domain-annotation-pipeline-"
USERNAME=sillitoe
REMOTE=ghcr.io

# docker compose -f docker-compose.cs.yml build
#
# GHCR_TOKEN=<generate github PAT token with read:packages, write:packages, delete:packages>
# 
# To pull the singularity sif file onto the HPC server:
#
# export SINGULARITY_DOCKER_USERNAME=${USERNAME}
# export SINGULARITY_DOCKER_PASSWORD=${GHCR_TOKEN}
# singularity pull docker://${REMOTE}/${USERNAME}/domain-annotation-pipeline-chainsaw:latest

docker login $REMOTE

for image_name in $(docker image ls | grep "^${DOCKER_STUB}" | awk '{print $1}' | sort -u); do
    echo "Processing image: ${image_name}"
    
    IMAGE_TAG_NAME="${REMOTE}/${USERNAME}/${image_name}"

    # Check if the image is already tagged
    if docker image ls | grep -q "$IMAGE_TAG_NAME"; then
        echo "Image ${IMAGE_TAG_NAME} already exists, skipping tagging."
    else
        # Tag the image
        echo "Tagging image ${image_name} as ${IMAGE_TAG_NAME}:latest"
        docker tag "${image_name}:latest" "${IMAGE_TAG_NAME}:latest"
    fi

    docker push ${IMAGE_TAG_NAME}:latest

done

