## Building docker image

```
docker build -t tasi-demo .
```

## Executing commands with Docker

```
docker run --mount type=bind,src=$(pwd),dst=/demo tasi-demo bash -c "<cmd>"
```

e.g. to make the test:

```
docker run --mount type=bind,src=$(pwd),dst=/demo tasi-demo bash -c "make test"
```
