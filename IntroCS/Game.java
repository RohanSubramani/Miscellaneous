//******************************
//	Game class for Pig
//  
//  This class models the game for Pig
//  the no-argument constructor has been slightly modified
//  so that it is compatible with the modifications we made to Player
//  The play method has been slightly modified to include more of the print
//  statements previously in the Player class
//  
//  You need to add a play method that takes an int parameter indicating
//  how many games to play and returns the number of games one by p1.
//
//******************************


import java.util.Scanner;

public class Game {

    private Player p1;  //human player 
    private Player p2;  //computer player
    
    // default constructor for interactive play
    public Game(){
        p1=new Player();
        p2=new Player(20); // create a computer player with threshold 20
    }
    // constructor to use for simulated play
    public Game(int first, int second){
        p1=new Player(first);
        p2=new Player(second);
    }

    public void play() {

        while(p1.getScore()<100 && p2.getScore()<100) {
            p1.play();
            if(p1.getScore()<100){
	            p2.play();
                System.out.println("Computer is done");
                System.out.println("Computer total score is: " + p2.getScore());
            }
	    }
	    if(p1.getScore()>=100)
		    System.out.println("You win!");
	    else
		    System.out.println("You lose!");

    } 

    public int play(int repeats) {
        // Declare counters
        int gamesPlayed = 0;
        int p1Wins = 0;
        
        // While counter < limit
        while (gamesPlayed < repeats)
        {
            while (p1.getScore() < 100 && p2.getScore() < 100)
            {
                //p1 plays, if they don't win, p2 plays.p1
                p1.play();
                if(p1.getScore()<100)
                {
	                p2.play();
                    // Don't want print statements in a long simulation!!
                }
                if (p1.getScore() >= 100)
                {
                    p1Wins++;
                }
            }
            gamesPlayed++;
            p1.reset();
            p2.reset();
        }
        return p1Wins;
    } // end of new play method

    
   
} // end class  
