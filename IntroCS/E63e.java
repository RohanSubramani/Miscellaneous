/**
 * This program prints the positions of all vowels in an inputted string.
 * 
 * @author: Rohan Subramani
 * @date: 2/14/2021
 */

import java.util.Scanner;

public class E63e{
    public static void main(String[] args){
        
        Scanner input = new Scanner(System.in);
        System.out.println("Enter a string, and I will tell you the positions within the string which are vowels: ");
        String s = input.nextLine();
        String a = "";
        String vowels = "aeiouAEIOU";
        
        System.out.println("There are vowels at the following positions (1 means the first character is a vowel, 2 means the 2nd character is a vowel, etc.): ");
        for (int i = 0; i<s.length(); i++)
        {
            a = s.substring(i,i+1);
            if (vowels.contains(a))
            {
                System.out.println(i+1);
            }
        }
    }   
}