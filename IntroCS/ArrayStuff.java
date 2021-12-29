
//********************************************************************
//  ArrayStuff.java    
//
//  Repository for some static methods for manipulating arrays
//  
//********************************************************************

public class ArrayStuff{
    
    
    /* returns a new array containing only the elements
     *  of stuff that were at even indices*/
    public static int[] evenIndices(int[] stuff){
        // Create answer array with correct length
        int[] answer;
        if (stuff.length%2 == 0)
        {
            answer = new int[stuff.length/2];
        }
        else
        {
            answer = new int[stuff.length/2 + 1];
        }
        
        // Populate answer array with elements at even indices of stuff
        for (int i = 0; i<stuff.length; i++)
        {
            if(i%2 == 0)
            {
                answer[i/2] = stuff[i];
            }
        }
        return answer;
    }
    
        
    /* returns a new array containing only the elements
     *  of stuff that have even values*/
    public static int[] evenValues(int[] stuff){
        // Count number of even values in stuff
        int evens = 0;
        for (int element: stuff)
        {
            if (element%2 == 0)
            {
                evens++;
            }
        }
        
        // Add even valued elements to answer array
        int[] answer = new int[evens];
        int i = 0;
        for (int element: stuff)
        {
            if (element%2 == 0)
            {
                answer[i] = element;
                i++;
            }
        }
        return answer;
        
    }    
        
    /* returns a new array with the elements
     *  of stuff in reverse order*/
    public static int[] reverse(int[] stuff){
        int[] answer = new int[stuff.length];
        
        for (int i = 0; i<answer.length; i++)
        {
            answer[i] = stuff[stuff.length - 1 - i];
        }
        
        return answer;
    }
    
    
    /* returns a new array of length two that
     * has the last element of stuff first and
     * the first element of stuff last */
    public static int[] lastWillBeFirst(int[] stuff){
        int[] answer = new int[2];
        
        answer[0] = stuff[stuff.length - 1];
        answer[1] = stuff[0];
        
        return answer;
    }
}