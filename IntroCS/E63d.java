/**
 * This program prints the number of vowels in an inputted string.
 * 
 * @author: Rohan Subramani
 * @date: 2/14/2021
 */

import java.util.Scanner;

public class E63d{
    public static void main(String[] args){
        
        Scanner input = new Scanner(System.in);
        System.out.println("Enter a string, and I will tell you how many vowels it has: ");
        String s = input.nextLine();
        int result = 0;
        String a = "";
        String vowels = "aeiouAEIOU";
        
        for (int i = 0; i<s.length(); i++)
        {
            a = s.substring(i,i+1);
            if (vowels.contains(a))
            {
                result++;
            }
        }
        System.out.println(result);
    }   
}