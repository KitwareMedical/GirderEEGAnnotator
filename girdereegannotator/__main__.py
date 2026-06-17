from girdereegannotator.core import AnnotatorApp


def main(**kwargs) -> None:
    app = AnnotatorApp()
    app.server.start(**kwargs)


if __name__ == "__main__":
    main()
