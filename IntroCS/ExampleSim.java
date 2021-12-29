//******************************
//	Example Test class simulating Pig computer vs. computer
//  
//  Your Game class must work with this class.
//
//
//******************************




public class ExampleSim {

    public static void main(String[] args) {
        
        Game g = new Game(15,5);
        int p1Wins=g.play(1000);
        System.out.println("player 1 wins: "+ p1Wins + " games!");
           
        
    } // end main   
} // end class  
