"""The mcp-greenroom command. Talks to the API over HTTP only."""

import typer

app = typer.Typer()


@app.callback(invoke_without_command=True)
def main() -> None:
    pass
