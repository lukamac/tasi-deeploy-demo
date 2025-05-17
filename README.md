In this demo we will use the prebuilt docker image of Deeploy to circumvent installing the necessary toolchain and emulation.

## Docker

### Building the image

```
docker build -t tasi-demo .
```

### Executing commands

```
docker run --mount type=bind,src=$(pwd),dst=/demo tasi-demo bash -c "<cmd>"
```

e.g. to make the test:

```
docker run --mount type=bind,src=$(pwd),dst=/demo tasi-demo bash -c "make test"
```

## Getting Deeploy

```
pip install git+https://github.com/pulp-platform/Deeploy.git@devel
```

Once you have familiarized yourself enough with Deeploy and want to change the internals, do an editable install:

```
git clone https://github.com/pulp-platform/Deeploy.git --branch devel
pip install --editable Deeploy
```

If you decide that you'd like to contribute your changes back to upstream, just create a fork of Deeploy, push your changes there, and create a PR :)
