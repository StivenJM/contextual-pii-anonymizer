import uvicorn

from app import create_app


app = create_app()


def run() -> None:
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    run()
