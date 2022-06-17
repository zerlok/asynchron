# asynchron

Python service framework with code generator based on AsyncAPI specification

## Usage example

1) install and run codegen
    ```bash
    poetry add asynchron -E cli
    poetry run asynchron -f /path/to/asyncapi.yaml codegen python-aio-pika -o /output/dir
    ```
2) install dependencies for you generated code
    ```bash
    poetry add asynchron -E aio-pika
    ```

## Development

Use bash script to install all necessary dependencies. It installs all defined extras from `pyproject.toml`

```bash
./scripts/install-dev.sh
```
