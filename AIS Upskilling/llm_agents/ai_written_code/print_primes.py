import sys

def is_prime(num):
    if num < 2:
        return False
    for i in range(2, int(num**0.5) + 1):
        if num % i == 0:
            return False
    return True

def print_n_primes(n):
    count, num = 0, 2
    while count < n:
        if is_prime(num):
            print(num)
            count += 1
        num += 1

if __name__ == '__main__':
    n = int(sys.argv[1])
    print_n_primes(n)
