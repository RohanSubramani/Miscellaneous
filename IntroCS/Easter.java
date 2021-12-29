/**
 * This program implements the algorithm created by Fredrich Gauss 
 * for determining the date of Easter
 * 
 * @author: <your name here>
 * @date: <the date here>
 */

import java.util.Scanner;

public class Easter{
  
    public static void main(String[] args){

        Scanner input = new Scanner(System.in);
        System.out.println("Enter the year: ");
        int y = input.nextInt();
        int a, b, c, d, e, g, h, j, k, m, n, r, p;
        
        a = y%19;
        b = y/100;
        c = y%100;
        d = b/4;
        e = b%4;
        g = (8*b+13)/25;
        h =  (19 * a + b - d - g + 15)%30;
        j = c/4;
        k = c%4;
        m =  (a + 11 * h)/319;
        r = (2 * e + 2 * j - k - h + m + 32)%7;
        n = (h - m + r + 90)/25;
        p = (h - m + r + n + 19) % 32;
        
        String[] months = 
        {
            "Jan", "Feb", "Mar", "April", "May", "June", "July", "August", "September",
            "October", "November", "December"
        };
        // I looked up how to make a list to avoid having 12 if/esle if statements. I don't know if there was another more efficient way. 
        String month = months[n-1];
        
        System.out.println("In the year " + y + ", Easter falls on " + month + " " + p + ".");
        
    }

}	
