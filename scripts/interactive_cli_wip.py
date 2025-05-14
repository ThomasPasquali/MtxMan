
def get_dataset_size():
    while True:
        show_sizes_menu()
        size = input("Enter your choice (1-3): ").strip()
        if size == "1":
            return "small"
        elif size == "2":
            return "large"
        elif size == "3":
            exit()
        else:
            print("Invalid choice. Please enter a number from 1 to 3.")


def show_sizes_menu():
    print("\nChoose the size of data to produce:\n")
    print("1. small")
    print("2. large")
    print("3. Exit program\n")


def show_sources_menu():
    print("\nChoose your source of data:\n")
    print("1. generators")
    print("2. suite sparce matrix list")
    print("3. suite sparce matrix range")
    print("4. Exit program\n")


def show_generators_menu():
    print("\nChoose what generator of data to use:\n")
    print("1. graph500")
    # print("2. Matrix Market")
    print("2. Exit program\n")


if __name__ == "__main__":
    while True:
        size = get_dataset_size()
        show_sources_menu()
        choice = input("Enter your choice (1-4): ").strip()
        if choice == "1":
            print("generators option has been selected")
            show_generators_menu()
            choice = input("Enter your choice (1-2): ").strip()
            if choice == "1":
                graph500_generator.generate(config, size)
        elif choice == "2":
            print("suite sparce matrix list option has been selected\n")
            suite_sparse_matrix_downloader.download_list(config, size)
        elif choice == "3":
            print("suite sparce matrix range option has been selected")
            suite_sparse_matrix_downloader.download_range(config, size)
        elif choice == "4":
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please enter a number from 1 to 4.")