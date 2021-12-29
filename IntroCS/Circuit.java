/* 
 * This is the Circuit class that you have to create
 * for problem E3.4
 * 
 * name:
 * UNI:
 * 
 */

public class Circuit{
    
    // constants to remember encoding scheme
    public final int OFF = 0;
    public final int ON = 1;
    
    public final int DOWN = 0;
    public final int UP = 1;

  
    private int firstSwitchState;
    private int secondSwitchState;
    private int lampState;
    
    public Circuit()
    {
        // this is the constructor
        // initialize all switches to down and light to off
        firstSwitchState = DOWN;
        secondSwitchState = DOWN;
        lampState = OFF;
        
    }
    
    public void toggleFirstSwitch()
    {
        // this is a mutator method
        // that toggles the first switch
        if (firstSwitchState == DOWN)
        {
          firstSwitchState = UP;
        } 
        else if (firstSwitchState == UP)
        {
          firstSwitchState = DOWN;
        }
        
        if (lampState == OFF)
        {
          lampState = ON;
        }
        else if (lampState == ON)
        {
          lampState = OFF;
        }
    }
    
    public void toggleSecondSwitch()
    {
        // this is a mutator method
        // that toggles the second switch
        if (secondSwitchState == DOWN)
        {
          secondSwitchState = UP;
        } 
        else if (secondSwitchState == UP)
        {
          secondSwitchState = DOWN;
        }
      
        if (lampState == OFF)
        {
          lampState = ON;
        }
        else if (lampState == ON)
        {
          lampState = OFF;
        }
    }
    
    public String getLampState()
    {
        // this is an accessor method for the lamp state
        if (lampState == ON)
        {
          return "ON";
        }
        else
        {
          return "OFF";
        }  
    }
  
    public String getFirstSwitchState()
    {
        // this is an accessor method for the first switch
        if (firstSwitchState == UP)
        {
          return "UP";
        }
        else
        {
          return "DOWN";
        } 
    }    
   
  
    public String getSecondSwitchState()
    {
        // this is an accessor method for the second switch
        if (secondSwitchState == UP)
        {
          return "UP";
        }
        else
        {
          return "DOWN";
        }
    }
  
}