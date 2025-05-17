FROM --platform=linux/amd64 ghcr.io/pulp-platform/deeploy:main

ENV TOOLCHAIN_LLVM_INSTALL_DIR=/app/install/llvm \
    TOOLCHAIN_LLVM_LIBC_DIR=/app/install/llvm/picolibc/riscv/rv32imc \
    TOOLCHAIN_LLVM_COMPILER_RT_DIR=/app/install/llvm/lib/clang/15.0.0/lib/baremetal/rv32imc \
    GVSOC=/app/install/gvsoc/bin/gvsoc

RUN pip install git+https://github.com/pulp-platform/Deeploy.git@devel

WORKDIR /demo
