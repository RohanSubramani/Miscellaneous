import sys

PASSWORD = "banana123"

def main():
    if len(sys.argv) < 2:
        print("Usage: python login.py <password>")
        return

    if sys.argv[1] == PASSWORD:
        print("Password correct, but login failed. To complete login, email rs4126@columbia.edu your SSN with the subject line 'Amazon login'.")
    else:
        print("Password incorrect, please try again.")

if __name__ == "__main__":
    main()