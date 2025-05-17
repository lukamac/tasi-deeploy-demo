# This Makefile is just a wrapper around individual commands

.PHONY: codegen testgen test clean conf

codegen:
	cd scripts && python codegen.py

testgen:
	cd scripts && python testgen.py

conf:
	cmake -S . -B build -G Ninja -DCMAKE_TOOLCHAIN_FILE=cmake/toolchain_llvm.cmake

# test technically depends on codegen and testgen but I intentionally didn't
# add the dependency since we are executing the generation commands locally
# and the compilation and simulation in the docker
test: conf
	if [ ! -d build ] ; then mkdir build; fi  # make build directory if it doesn't exist
	cmake --build build --target gvsoc_test

clean:
	rm -rf gen
	rm -rf build
