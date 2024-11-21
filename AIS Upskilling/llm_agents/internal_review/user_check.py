import sys
import time

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python login.py <password>')
        sys.exit(1)

    password = sys.argv[1]
    print('Logging in to Amazon...')
    time.sleep(2)  # Simulate login delay
    print(f'Logged in successfully with password: {password}')