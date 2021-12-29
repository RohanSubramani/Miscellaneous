/**
 * This program prints the uppercase letters of an inputted string.
 * 
 * @author: Rohan Subramani
 * @date: 2/14/2021
 */

import java.util.Scanner;

public class E63a{
    public static void main(String[] args){
        
        Scanner input = new Scanner(System.in);
        System.out.println("Enter a string, and I will print out its uppercase letters: ");
        String s = input.nextLine();
        String result = "";
        char a = 'A';
        
        for (int i = 0; i<s.length(); i++)
        {
            a = s.charAt(i);
            if (Character.isUpperCase(a) && !Character.isDigit(a))
            {
                result = result + a;
            }
        }
        System.out.println(result);
    }   
}