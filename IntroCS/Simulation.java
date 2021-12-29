/**
 * This class should run simulations to determine
 * whether or not the Odd-Even game is fair and if
 * not who has the advantage and what is a strategy
 * that will realize that adavantage.
 *  
 *  UNI: rs4126
 *  Name: Rohan Subramani
 *  Feb 2021
 * 
 */


public class Simulation{
    
    public static void main(String[] args){
    
// NOTE: I use the word "best" many times here, but I don't really mean best 
// outright. I mean "best, assuming the other player uses the best possible 
// counter-strategy no matter what." 

// FINDING BEST STRATEGY FOR P1 
        
        double p1AvgWinnings = 5.0; // Higher than possible
        double p1MinAvgWinnings = 5.0; // Higher than possible
        double bestt1 = -1;
        double bestP1MinAvgWinnings = -5;
        
        for (double t1 = 0; t1 <= 1; t1 = t1 + .02)
        {
            p1MinAvgWinnings = 5.0; // Reset for each new t1
            for (double t2 = 0; t2 <= 1; t2 = t2 + .02)
            {
                Game g = new Game(t1,t2); 
                g.play(50000);
                p1AvgWinnings = g.getP1Score() / 50000.0;
                if (p1AvgWinnings < p1MinAvgWinnings)
                {
                    p1MinAvgWinnings = p1AvgWinnings;
                }
            }
            if (p1MinAvgWinnings > bestP1MinAvgWinnings)
            {
                bestt1 = t1;
                bestP1MinAvgWinnings = p1MinAvgWinnings;
            }
        }
        System.out.println("Best P1 Min Avg = " + bestP1MinAvgWinnings + " tokens.");
        System.out.println("Best t1 = " + bestt1 + ".");
        
// FINDING BEST STRATEGY FOR P2
        
        double p2AvgWinnings = 5.0; // Higher than possible
        double p2MinAvgWinnings = 5.0; // Higher than possible
        double bestt2 = -1;
        double bestP2MinAvgWinnings = -5;
        
        for (double t2 = 0; t2 <= 1; t2 = t2 + .02)
        {
            p2MinAvgWinnings = 5.0; // Reset for each new t2
            for (double t1 = 0; t1 <= 1; t1 = t1 + .02)
            {
                Game g = new Game(t1,t2); 
                g.play(50000);
                p2AvgWinnings = g.getP2Score() / 50000.0;
                if (p2AvgWinnings < p2MinAvgWinnings)
                {
                    p2MinAvgWinnings = p2AvgWinnings;
                }
            }
            if (p2MinAvgWinnings > bestP2MinAvgWinnings)
            {
                bestt2 = t2;
                bestP2MinAvgWinnings = p2MinAvgWinnings;
            }
        }
        System.out.println("Best P2 Min Avg = " + bestP2MinAvgWinnings + " tokens.");
        System.out.println("Best t2 = " + bestt2 + ".");    
    
// CONCLUSION
    
        if (bestP1MinAvgWinnings > 0)
        {
            System.out.println("P1 has an advantage in this game.\n"
                               + "By selecting a threshold t* of " + bestt1 + ","
                               + " P1 will \nwin tokens in the long run, regardless"
                               + " of P2's strategy.");
        }
        else if (bestP2MinAvgWinnings > 0)
        {
            System.out.println("P2 has an advantage in this game.\n"
                               + "By selecting a threshold t* of " + bestt2 + ","
                               + " P2 will \nwin tokens in the long run, regardless"
                               + " of P1's strategy.");
        }
        else
        {
            System.out.println("Neither player has an advantage." 
                               + "This is a fair game.");
        }
    }   
}