# asynchron
Python service framework with code generator based on AsyncAPI specification

## Usage example

1) install and run codegen
    ```bash
    poetry add asynchron -E codegen
    poetry run asynchron-codegen -f /path/to/asyncapi.yaml generate python-aio-pika -o /output/dir
    ```
2) install dependencies for you generated code
    ```bash
    poetry add asynchron -E aio-pika
    ```
