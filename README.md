## Structure

- `cmake`: extra cmake files
- `gen`: all the generated files will go here - C and hex files
- `kernel`: custom C kernel implementations
- `networks`: onnx networks and test input/output files for code generation
- `scripts`: python scripts for code and test generation
- `test`: C files necessary to build a full test app
- `third_party`: third party libraries
- `util`: utility C files


## Docker

In this demo we will use the prebuilt docker image of Deeploy to circumvent installing the necessary toolchain and emulation.

### Building the image

```
docker build -t tasi-demo .
```

### Executing commands

```
docker run --rm --tty --mount type=bind,src=$(pwd),dst=/demo tasi-demo bash -c "<cmd>"
```

e.g. to make the test:

```
docker run --mount type=bind,src=$(pwd),dst=/demo tasi-demo bash -c "make test"
```

## Deeploy

[Documentation](https://pulp-platform.github.io/Deeploy/branch/devel/)

Templating language used by Deeploy: [Mako](https://www.makotemplates.org/)

### Getting Deeploy

```
pip install git+https://github.com/pulp-platform/Deeploy.git@devel
```

Once you have familiarized yourself enough with Deeploy and want to change the internals, do an editable install:

```
git clone https://github.com/pulp-platform/Deeploy.git --branch devel
pip install --editable Deeploy
```

If you decide that you'd like to contribute your changes back to upstream, just create a fork of Deeploy, push your changes there, and create a PR :)
