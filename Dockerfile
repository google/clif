# Copyright 2020-2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This Dockerfile provides a base image with the libraries needed to compile
# and test CLIF preinstalled. Example workflow using this image:
#
#  // Build docker image
#  docker build $CLIF_DIR --tag clif --build-arg=UBUNTU_VERSION=18.04 ...
#
#  // Configure build
#  docker run --volume $CLIF_DIR:/clif --workdir /clif/build clif cmake ..
#
#  // Build clif-matcher
#  docker run --volume $CLIF_DIR:/clif --workdir /clif/build clif make clif-matcher
#
#  // Run cc tests
#  docker run --volume $CLIF_DIR:/clif --workdir /clif/build clif ctest
#
# This docker image can be customized using the following build args:
#
#  UBUNTU_VERSION: one of tags listed on https://hub.docker.com/_/ubuntu
#  ABSL_VERSION: one of abseil/abseil-cpp Github releases
#  PROTOBUF_VERSION: one of protocolbuffers/protobuf Github releases
#  PYTHON_VERSION: python version to use (>= 3.8)

ARG UBUNTU_VERSION=20.04

FROM ubuntu:${UBUNTU_VERSION}

ARG LLVM_VERSION_MAJOR=11
ARG ABSL_VERSION=20230125.1
ARG PROTOBUF_VERSION=22.0
ARG PYTHON_VERSION=3.10

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    curl \
    gpg-agent \
    g++ \
    libtool \
    make \
    pkg-config \
    software-properties-common \
    wget \
    unzip

# Configure LLVM apt repository
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add - && \
    add-apt-repository "deb http://apt.llvm.org/$(lsb_release -sc)/ llvm-toolchain-$(lsb_release -sc)-${LLVM_VERSION_MAJOR} main"

# Install CLIF dependencies
RUN apt-get update && apt-get install -y \
    clang-${LLVM_VERSION_MAJOR} \
    libclang-${LLVM_VERSION_MAJOR}-dev \
    libllvm${LLVM_VERSION_MAJOR} \
    llvm-${LLVM_VERSION_MAJOR} \
    llvm-${LLVM_VERSION_MAJOR}-dev \
    llvm-${LLVM_VERSION_MAJOR}-linker-tools \
    python3-dev \
    zlib1g-dev \
    libgtest-dev

# Configure deadsnakes PPA with the more recent versions of python packaged for
# Ubuntu. See https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa
RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y \
    "python$PYTHON_VERSION-dev" \
    "python$PYTHON_VERSION-distutils"

# Install latest version of pip since the version on ubuntu could be outdated
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    "python$PYTHON_VERSION" get-pip.py && \
    rm get-pip.py

# Compile and install absl-cpp from source
RUN wget "https://github.com/abseil/abseil-cpp/archive/$ABSL_VERSION.tar.gz" && \
    tar -xf "$ABSL_VERSION.tar.gz" && \
    mkdir "abseil-cpp-$ABSL_VERSION/build" && \
    cd "abseil-cpp-$ABSL_VERSION/build" && \
    cmake .. -DBUILD_SHARED_LIBS=ON && \
    make -j$(nproc) && \
    make install && \
    rm -rf "/abseil-cpp-$ABSL_VERSION" "/$ABSL_VERSION.tar.gz"

# Compile and install protobuf from source
RUN wget "https://github.com/protocolbuffers/protobuf/releases/download/v$PROTOBUF_VERSION/protobuf-$PROTOBUF_VERSION.tar.gz" && \
    tar -xf "protobuf-$PROTOBUF_VERSION.tar.gz" && \
    cd "protobuf-$PROTOBUF_VERSION" && \
    cmake . -DBUILD_SHARED_LIBS=ON -DCMAKE_CXX_STANDARD=17 -Dprotobuf_BUILD_TESTS=OFF -Dprotobuf_ABSL_PROVIDER=package && \
    make -j$(nproc) && \
    make install && \
    ldconfig && \
    rm -rf "/protobuf-$PROTOBUF_VERSION" "/protobuf-$PROTOBUF_VERSION.tar.gz"

# Install googletest
RUN cd /usr/src/googletest && \
    cmake . && \
    make -j$(nproc) && \
    make install

# Install python runtime and test dependencies
RUN "python$PYTHON_VERSION" -m pip install \
    absl-py \
    parameterized \
    protobuf=="4.$PROTOBUF_VERSION" \
    pyparsing==2.2.2
