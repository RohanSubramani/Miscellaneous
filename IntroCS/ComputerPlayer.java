/**
 * This class represents a computer
 * player in the Odd-Even game
 * 
 *  UNI: rs4126
 *  Name: Rohan Subramani
 *  Feb 2021
 * 
 */

public class ComputerPlayer{
    private double t;
    private int tokenBalance;
    private double random;
    private int selection;
    
    public ComputerPlayer(double threshold){
        t=threshold;
        tokenBalance=0;
        random = -1.0;
        selection = 0;
    }
    
    public void select()
    {
        random = Math.random();
        if (random > t)
        {
            selection = 2;
        }
        else
        {
            selection = 1;
        }
    }
    
    public int getSelection()
    {
        return selection;
    }
    
    public void resetTokenBalance()
    {
        tokenBalance = 0;
    }
    
    public void payTokens(int tokens)
    {
        tokenBalance = tokenBalance - tokens;
    }
    
    public void winTokens(int tokens)
    {
        tokenBalance = tokenBalance + tokens;
    }
    
    public int getTokenBalance()
    {
        return tokenBalance;
    }
}