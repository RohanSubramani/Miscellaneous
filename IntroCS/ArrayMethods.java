/**
* ArrayMethods - Manipulate Array Contents
* 
* COMS W1004
* 
* Rohan Subramani
*
* 
*/

import java.util.Arrays;
import java.util.ArrayList;

public class ArrayMethods {

    // private instance variables
    private int[] values;
    // this is for  resetting purposes, otherwise not needed
    private int[] originalValues; 

    //constructor
    public ArrayMethods(int[] initialValues) {
        values = initialValues;
        originalValues = Arrays.copyOf(values, values.length);
    }

    // pretty printing for testing purposes
    public void printArray() {
        for (int i : values) {
            System.out.print(i + " ");
    }
        System.out.println("");
    }
    
    // resetting back to original values for testing purposes
    public void resetValues() {
        values = Arrays.copyOf(originalValues, originalValues.length);
    }

    // a. swap the first and last elements
    public void swapFirstAndLast() {
        int i = values[0];
        values[0] = values[values.length - 1];
        values[values.length - 1] = i;
    }

    // b. shift all element to right and wraparound
    public void shiftRight() {
        int i = values[values.length - 1];
        for (int j = values.length-1; j > 0; j--)
        {
            values[j] = values[j-1];
        }
        values[0] = i;
    }

    // c. replace even elements with zero
    public void replaceEven() {
        for (int i = 0; i<values.length; i++)
        {
            if (values[i]%2 == 0)
            {
                values[i] = 0;
            }
        }
    }

    // d. replace middle elements with larger of two neighbors
    public void replaceMiddle() {
        int[] answer = new int[values.length];
        answer[0] = values[0];
        answer[values.length-1] = values[values.length-1];
        for (int i = 1; i<values.length - 1; i++)
        {
            if (values[i-1]>=values[i+1])
            {
                answer[i] = values[i-1];
            }
            else
            {
                answer[i] = values[i+1];
            }
        }
        values = answer;
    }

    // e. Remove middle one or two elements
    public void removeMiddle() {
        int[] answer;
        if (values.length%2 == 1)
        {
            answer = new int[values.length-1];
            for (int i = 0; i<answer.length/2;i++)
            {
                answer[i] = values[i];
            }
            for (int i = answer.length-1; i>=answer.length/2;i--)
            {
                answer[i] = values[i+1];          
            }
        }
        else
        {
            answer = new int[values.length-2];
            for (int i = 0; i < answer.length/2;i++)
            {
                answer[i] = values[i];
            }
            for (int i = answer.length-1; i >= answer.length/2;i--)
            {
                answer[i] = values[i+2];         
            }
        }
        values = answer;
    }

    // f. Move even elements to the front
    public void moveEven() {
        int number_of_evens = 0;
        int number_of_odds = 0;
        for (int element: values)
        {
            if (element%2 ==0)
            {
                number_of_evens++;
            }
            else
            {
                number_of_odds++;
            }
        }
        int[] evens = new int[number_of_evens];
        int[] odds = new int[number_of_odds];
        int evens_counter = 0;
        int odds_counter = 0;
        for (int k: values)
        {
            if (k%2 == 0)
            {
                evens[evens_counter] = k;
                evens_counter++;
            }
            else
            {
                odds[odds_counter] = k;
                odds_counter++;
            }
        }
        int answer[] = new int[values.length];
        for (int i = 0; i<number_of_evens; i++)
        {
            answer[i] = evens[i];
        }
        for (int j = 0; j<number_of_odds; j++)
        {
            answer[number_of_evens+j] = odds[j];
        }
        values = answer;
    }

    // g. Return the value of the second-largest element
    public int secondLargest() {
        int max = 0;
        int secondLargest = 0;
        for (int i: values)
        {
            if (i>max)
            {
                secondLargest = max;
                max = i;
            }
            else if (i>secondLargest && i < max) 
                // Ignore it if it equals either
            {
                secondLargest = i;
            }
        }
        return secondLargest;
    }

    // h. Check if sorted in increasing order
    public boolean sortedIncreasing() {
        boolean isIncreasing = true;
        for (int i = 1; i<values.length; i++)
        {
            if (values[i] < values[i-1])
            {
                isIncreasing = false;
            }
        }
        return isIncreasing;
    }

    // i. Check if contains two adjacent duplicate elements
    public boolean adjacentDups() {
        boolean areAdjDups = false;
        for (int i = 1; i<values.length; i++)
        {
            if (values[i] == values[i-1])
            {
                areAdjDups = true;
            }
        }
        return areAdjDups;
    }

    // j. Check if contains any duplicate elements
    public boolean containsDups() {
        boolean areDups = false;
        for (int j = 0; j<values.length-1;j++)
        {
            for (int i = j+1; i<values.length; i++)
            {
                if (values[i] == values[j])
                {
                    areDups = true;
                }
            }
        }
        return areDups;
	}
}
