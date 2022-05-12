FROM ubuntu:focal

ARG USER=root
ARG UID=0
# Could have name this argument as GID but to conform the naming convention
# in most Linux distributions...
ARG GROUPS=0
ARG HOME=/root

RUN if [ ${UID} -ne 0 ]; then \
        addgroup --gid ${GROUPS} ${USER}; \
        useradd ${USER} -m -u ${UID} -g ${GROUPS} -G sudo; \
    fi

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get -y upgrade && \
    apt-get -y install \
        cmake gcc build-essential libtinfo-dev valgrind sudo \
        zlib1g-dev python3-distutils python3-pip python3-setuptools \
        git apt-utils bear virtualenv libboost-all-dev \
        ninja-build autoconf libtool automake libpcre3-dev \
        gettext rsync wget texinfo gperf autopoint pkg-config libxml2-dev \
        libmount-dev libsigc++-2.0-dev mm-common time locales-all \
        libssl-dev bison libtool-bin subversion screen parallel \
        coz-profiler && \
    rm -rf /var/lib/apt/lists/*$ && \
    pip3 install meson && passwd -d ${USER} && \
    groupadd mysql && useradd -r -g mysql -s /bin/false mysql

# WORKDIR /root
# RUN git clone --branch release/9.x --depth=1 https://github.com/llvm/llvm-project && \
#     git clone https://github.com/GNOME/glib/ && \
#     git clone https://github.com/GNOME/glibmm

RUN cd /root && \
    git clone \
        --branch release/10.x \
        --depth=1 \
        https://github.com/llvm/llvm-project && \
    mkdir llvm_build && cd llvm_build && \
    cmake -GNinja \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/usr \
        -DLLVM_INCLUDE_TESTS=OFF \
        -DLLVM_INCLUDE_EXAMPLES=OFF \
        -DLLVM_INCLUDE_BENCHMARKS=OFF \
        -DLLVM_INCLUDE_DOCS=OFF \
        -DLLVM_ENABLE_RTTI=ON \
        -DLLVM_OPTIMIZED_TABLEGEN=ON \
        -DLLVM_ENABLE_PROJECTS="llvm;clang;libcxx;libcxxabi;lld;compiler-rt;clang-tools-extra" \
        -DCOMPILER_RT_INCLUDE_TESTS=OFF \
        -DLLVM_TARGETS_TO_BUILD=X86 \
        /root/llvm-project/llvm/ && \
    ninja install && \
    cd /root && \
    rm -rf llvm-project llvm_build

ENV CC=clang
ENV CXX=clang++

# note: does not work if root user
WORKDIR /home/$USER
CMD /bin/bash
