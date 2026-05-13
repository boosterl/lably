from lably.core.i18n import setup_i18n
from lably.ui import create_main_window


def main() -> None:
    setup_i18n()
    window = create_main_window()
    window.show()


if __name__ == "__main__":
    main()
