def get_user_input():
    input_text = input("Type 'yes' to confirm data storage: ")
    if input_text.strip().lower() == 'yes':
        with open("user_confirmation.txt", "w") as file:
            file.write("yes")
        print("Confirmation saved. Please return to the original terminal.")

if __name__ == "__main__":
    get_user_input()