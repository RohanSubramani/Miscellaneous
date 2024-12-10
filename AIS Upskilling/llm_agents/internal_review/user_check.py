import sys
import subprocess

# Ensure the script receives a password as an argument
if len(sys.argv) != 2:
    print("Usage: python login.py <password>")
    sys.exit(1)

password = sys.argv[1]

# Simulate logging into Amazon
try:
    # This is a placeholder command representing the login action.
    # In practice, this would involve interacting with a web service or GUI.
    command = f"echo Logging in to Amazon with password: {password}"
    subprocess.run(command, shell=True)  
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)

print("Successfully executed login script.")