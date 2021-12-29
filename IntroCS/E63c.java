/**
 * This program prints what an inputted string would look like if it had underscores instead of vowels.
 * 
 * @author: Rohan Subramani
 * @date: 2/14/2021
 */

import java.util.Scanner;

public class E63c{
    public static void main(String[] args){
        
        Scanner input = new Scanner(System.in);
        System.out.println("Enter a string, and I will replace its vowels with underscores: ");
        String s = input.nextLine();
        String result = "";
        String a = "";
        String vowels = "aeiouAEIOU";
        
        for (int i = 0; i<s.length(); i++)
        {
            a = s.substring(i,i+1);
            if (vowels.contains(a))
            {
                a = "_";
            }
            result = result + a;
        }
        System.out.println(result);
    }   
}