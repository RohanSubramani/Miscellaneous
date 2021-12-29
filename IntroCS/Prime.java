/**
 * This program accepts a positive integer as input and
 * determines whether or not the integer is prime.
 * 
 * @author: <your name here>
 * @date: <the date here>
 */

import java.util.Scanner;

public class Prime{
    
    public static void main(String[] args){
   
        // I made some changes from my pset response because I had overlooked a few things, I hope that's ok.
        Scanner scan = new Scanner(System.in);
        long N; // I was testing some big numbers and had problems, using "long" instead of "int" solved them.
        System.out.println("Want to know if a number is prime? Enter it here: ");
        N = scan.nextLong();
        if (N == 0 || N == 1)
        {
            System.out.println(N + " is not prime!");
        }
        else if (N == 2)
        {
            System.out.println(N + " is prime!");
        }
        else
        {
            double A = N/2.0;
            if (A == (int) A)
            {
                System.out.println("Not prime, 2 is a factor of " + N + ".");
            }

            double D = 3.0; // Even though D will always be an integer, I want to get doubles when using it in operations later.
            while (A != (int) A && A > D) // (A != (int) A && A > D) is true to begin with if N is odd unless N = 3
            {
                A = N/D;
                if (A == (int) A)
                {
                    System.out.println("Not prime, " + (int) D + " is a factor of " + N + ".");
                }
                else
                {
                    D = D + 2;
                }
            }
            if (A != (int) A)
            {
                System.out.println(N + " is prime!");
            }
        }    
    }
}
 