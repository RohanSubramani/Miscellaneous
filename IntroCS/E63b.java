/**
 * This program prints every second character from an inputted string.
 * 
 * @author: Rohan Subramani
 * @date: 2/14/2021
 */

import java.util.Scanner;

public class E63b{
    public static void main(String[] args){
        
        Scanner input = new Scanner(System.in);
        System.out.println("Enter a string, and I will print out every second character: ");
        String s = input.nextLine();
        String result = "";
        char a = 'A';
        
        for (int i = 1; i<s.length(); i = i+2)
        {
            a = s.charAt(i);
            result = result + a;
        }
        System.out.println(result);
    }   
}