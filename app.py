from src.ui import LAUNCH_KWARGS, create_app

app = create_app()

if __name__ == "__main__":
    app.launch(**LAUNCH_KWARGS)
