RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\x1b[33m"


def color_red(text):
    return f"{RED}{text}{RESET}"


def color_green(text):
    return f"{GREEN}{text}{RESET}"


def color_yellow(text):
    return f"{YELLOW}{text}{RESET}"
