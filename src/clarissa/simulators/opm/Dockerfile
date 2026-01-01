# Dockerfile for OPM Flow - Open Porous Media Reservoir Simulator
# Based on Ubuntu 22.04 LTS

FROM ubuntu:22.04

LABEL maintainer="OPM Flow Docker"
LABEL description="Open Porous Media Flow Reservoir Simulator"

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set locale
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install dependencies and add OPM repository
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add OPM official repository
RUN apt-add-repository ppa:opm/ppa

# Install OPM Flow and related packages
RUN apt-get update && apt-get install -y \
    mpi-default-bin \
    libopm-simulators-bin \
    && rm -rf /var/lib/apt/lists/*

# Create a working directory for simulation data
WORKDIR /simulation

# Default command - show OPM Flow version
CMD ["flow", "--version"]
