//*************************************
//
//  WordLists.java
//
//  Class to aid with Scrabble
//  Programming Project 5, COMS W1004
//
//  4/11/2021
//  Name: Rohan Subramani
//  Uni: rs4126
//**************************************

import java.util.ArrayList;
import java.util.Scanner;
import java.io.*;

public class WordLists{
    
    private File inFile;
    private Scanner input;
    private ArrayList<String> allWords;

    public WordLists(String fileName) throws FileNotFoundException{

        inFile = new File(fileName);
// Possible FileNotFoundException        
        input = new Scanner(inFile);
        allWords = new ArrayList<String>();
        String word;
        while(input.hasNext())
        {
            word=input.next();
            allWords.add(word);
        }
    }
    
// Return an ArrayList of all length n words (Strings) in the dictionary file
    public ArrayList<String> lengthN(int n){

        if(n<1) // No words less with 0 or negative letters
// No 1-letter words either, but it makes sense to get a blank list for that    
            throw new IllegalArgumentException();
        ArrayList<String> wordList = new ArrayList<String>();
        for (String word: allWords) 
        {
            if (word.length() == n)
            {
                wordList.add(word);
            }
        }
        return wordList;
        
//         EXCEPTIONS?
    }

// Return an ArrayList of words of length n ending with the letter lastLetter
    public ArrayList<String> endsWith(char lastLetter, int n){
        
        ArrayList<String> wordList = new ArrayList<String>();
        ArrayList<String> nLength = new ArrayList<String>();
        nLength = this.lengthN(n); // List of all words with n letters
        for (String element: nLength)
        {
            if (element.charAt(element.length()-1) == lastLetter)
            {
                wordList.add(element);
            }
        }
        return wordList;
        
//         EXCEPTIONS?
    }

// Return an ArrayList of words of length n containing the letter included
// at position index
    public ArrayList<String> containsLetter(char included, int index, int n){

        ArrayList<String> wordList = new ArrayList<String>();
        ArrayList<String> nLength = new ArrayList<String>();
        nLength = this.lengthN(n); // List of all words with n letters
        for (String element: nLength)
        {
            if (element.charAt(index) == included)
            {
                wordList.add(element);
            }
        }
        return wordList;
        
//         EXCEPTIONS?
    }

//  Return ArrayList of words with exactly m occurrences of the letter included 
    public ArrayList<String> multiLetter(int m, char included){
        
        if(m<0) // No fewer than 0 instances of a letter in a word    
            throw new IllegalArgumentException();ArrayList<String> wordList = new ArrayList<String>();
        int n = 0; // Track  number of times "included" appears in word
        for (String word: allWords)
        {
            n = 0; // Need to reset for each word
            for (int i = 0; i<word.length(); i++)
            {
                if (word.charAt(i) == included)
                {
                    n++;
                }
            }
            if (n == m)
            {
                wordList.add(word);
            }
        }
        return wordList;
        
//         EXCEPTIONS?

    }

} // end of class








