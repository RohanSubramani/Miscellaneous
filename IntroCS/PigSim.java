//******************************
//	Test class simulating Pig computer vs. computer
//  
//  play 1000 games against each other and report 
//  the winning percentage of player 1
//
//
//******************************




public class PigSim {

    public static void main(String[] args) {
        
        final int T1 = 10;
        final int T2 = 20;
        final int SIMNUM = 1000;
        
        // Declare and initialize a simulated game
        
        Game simGame = new Game(T1,T2);
        
        // Play a certain number of games
        int p1Wins = simGame.play(SIMNUM);
        double p1WinsDouble = p1Wins; // Like casting
        
        // Calculate a percent of p1 wins
        double p1WinPercentage = (p1WinsDouble/SIMNUM)*100;
        
        // Print results
        System.out.println("P1 has won " + p1WinPercentage + "% of games played.");
        
    } // end main   
} // end class  
