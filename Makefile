# This Makefile is just a wrapper around individual commands

.PHONY: all codegen testgen test clean conf

all: gen testgen test

codegen:
	cd scripts && python codegen.py

testgen:
	cd scripts && python testgen.py

conf:
	cmake -S . -B build -G Ninja -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain_llvm.cmake

test: codegen testgen conf
	if [ ! -d build ] ; then mkdir build; fi  # make build directory if it doesn't exist
	cmake --build build --target gvsoc_test

clean:
	rm -rf gen
	rm -rf build
