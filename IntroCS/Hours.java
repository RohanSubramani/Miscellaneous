/**
 * This program converts a number of days and weeks into the
 * equivalent number of hours
 * 
 * @author: <your name here>
 * @date: <the date here>
 */

import java.util.Scanner;

public class Hours{
    
    public static void main(String[] args){
        
        Scanner input = new Scanner(System.in);
        System.out.println("Enter a number of weeks: ");
        int weeks = input.nextInt();
        System.out.println("Enter a number of days: ");
        int days = input.nextInt();
        
        days = days + weeks*7;
        int hours = days*24;
        System.out.println("That is equal to " + hours + " hours.");
    }
}
 