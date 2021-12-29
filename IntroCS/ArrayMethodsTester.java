/**
* ArrayMethodsTester - Tester for Array Methods
* 
* COMS W1004
* 
* 
* 
* @author Kimberly Hou (kjh2146)
*/

public class ArrayMethodsTester {
    public static void main(String[] args){
        int[] x = { -1, 2, 4, 2, 7, 8, 9 };
        
        ArrayMethods am = new ArrayMethods(x);

        // original array
        am.printArray();
		
        // test a
        am.swapFirstAndLast();
        System.out.print("Swapping: ");
        am.printArray();
        am.resetValues();
		
		// test b
        am.shiftRight();
        System.out.print("Shifting right: ");
        am.printArray();
        am.resetValues();

        // test c
        am.replaceEven();
        System.out.print("Replacing even elements: ");
        am.printArray();
        am.resetValues();
        
        // test d
        am.replaceMiddle();
        System.out.print("Replacing middle elements: ");
        am.printArray();
        am.resetValues();

        // test e
        am.removeMiddle();
        System.out.print("Removing middle element(s): ");
        am.printArray();
        am.resetValues();

        // test f
        am.moveEven();
        System.out.print("Moving even elements: ");
        am.printArray();
        am.resetValues();

        // test g
        System.out.print("Second largest element: ");
        System.out.println(am.secondLargest());

        // test h
        System.out.print("Is sorted in increasing order: ");
        System.out.println(am.sortedIncreasing());

        // test i
        System.out.print("Has adjacent duplicates: ");
        System.out.println(am.adjacentDups());

        // test j
        System.out.print("Contains duplicates: ");
        System.out.println(am.containsDups());


    }

}
