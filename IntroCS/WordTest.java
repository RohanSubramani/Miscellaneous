//*************************************
//
//  WordTest.java
//
//  Test class for WordLists.java
//  Programming Project 5, COMS W1004
//
//  4/11/2021
//  Name: Rohan Subramani
//  Uni: rs4126
//**************************************

import java.util.ArrayList;
import java.io.*;

public class WordTest{
    public static void main(String[] args){ // throws FileNotFoundException
        try
        {
            WordLists wordlist = new WordLists("dictionary.txt");
            ArrayList<String> lengthN = wordlist.lengthN(28);
            PrintWriter output1 = new PrintWriter("lengthNoutput.txt");
            for (String word: lengthN)
            {
                output1.println(word);
            }
            output1.close();
            
            ArrayList<String> ends = wordlist.endsWith('l', 12);
            PrintWriter output2 = new PrintWriter("endsoutput.txt");
            for (String word: ends)
            {
                output2.println(word);
            }
            output2.close();
            
            ArrayList<String> contains = wordlist.containsLetter('x', 0, 9);
            PrintWriter output3 = new PrintWriter("containsoutput.txt");
            for (String word: contains)
            {
                output3.println(word);
            }
            output3.close();
            
            ArrayList<String> multi = wordlist.multiLetter(4, 'a'); 
            PrintWriter output4 = new PrintWriter("multioutput.txt");
            for (String word: multi)
            {
                output4.println(word);
            }
            output4.close();
        }
        
        catch(FileNotFoundException a)
        {
            System.out.println("There is no file with that name, try again!");
            System.out.println(a);
        }
        
        catch(IllegalArgumentException b)
        {
            System.out.println("You entered an invalid input, try again!");
            System.out.println("Negative or zero valued inputs "
                               + "may be the problem.");
            System.out.println(b);
        }
        
        catch(StringIndexOutOfBoundsException c)
        {
            System.out.println("Make sure your index input is between 0 "
                               + "and the word length!");
            System.out.println(c);
        }
    }
} // end of class






