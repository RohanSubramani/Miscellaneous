//******************************
//	models a Player in Pig
//  this class has been modified
//  
//    1) a threshold instance variable t has been added
//    2) the constructor has been changed
//    3) the contructor has been overloaded
//    4) the compPlay has fewer print statements
//    5) a new reset method has been added to reset score to 0
//    
//    
//******************************


import java.util.Scanner;

public class Player {

    private boolean isHuman;
    private int score;
    private Die myDie;
    private Scanner input;
    private int t;

    //default constructor will create a human player
    public Player(){
        isHuman = true; 	
	    myDie=new Die(6);
	    score=0;
	    input = new Scanner(System.in);
        // don't need to initialize t
	
    }
    
    public Player(int threshold){
        isHuman=false;
        myDie=new Die(6);
        score=0;
        t=threshold;
        // don't need to initialize the Scanner
    }


    public void play() {
	    if(isHuman)
	        playHuman();
	    else
	        playComp();
    }


    private void playHuman() {
	    int current=0;
	    int runningTotal=0;
	    int again=1;

	    while(again==1) {
	        myDie.roll();
	        current=myDie.getSide();
	        System.out.println("You rolled a " + current);
	        if (current == 1) {
	            again=0; 
	            runningTotal=0;
	        }
	        else {
	            runningTotal=runningTotal+current;
	            System.out.println("Your round total is now " + runningTotal);
	            System.out.println("Roll again? (1-yes, 0-no)");
	            again=input.nextInt();
	        }

	    }//end while
	    score=score+runningTotal;
	    System.out.println("Your total score is: " + score);
    }//end method
    
    private void playComp() {
	    int current=0;
	    int runningTotal=0;

	    while(runningTotal<t && current != 1 && score+runningTotal<100) {
	        myDie.roll();
	        current=myDie.getSide();
            // comment this out since we don't want it for the simulation.
	        // System.out.println("Computer rolled a " + current);
	        if (current == 1) {
	            runningTotal = 0;
	        }
	        else{
	            runningTotal = current+runningTotal;
            }
	    }//end while
	    score=score+runningTotal;
    } //end playComp


    public int getScore() {
	    return score;
    }

    public void reset(){
        score=0;
    }
} // end class  
