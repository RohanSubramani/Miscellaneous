/* 
 * This is the Car class that you have to create
 * for problem E3.13
 * 
 * name:
 * UNI:
 * 
 */

public class Car{
  
    //  for this problem don't worry about the maximum amount of gas
    //  allowed in the tank or tracking the overall miles driven
  
  
    private double gas;
    private double gasMileage;
    
    
    public Car(double efficiency)
    {
        // this is the constructor
        gas = 0.0;
        gasMileage = efficiency;
        
    }
    
    public void drive(double miles)
    {
        // this is a mutator method
        // that reduces the gas in the tank 
        gas = gas - miles/gasMileage ;
       
    }
    
    public void addGas(double gasAmount)
    {
        // this is a mutator method
        // that adds gas to the tank
        gas = gas + gasAmount;
    }
    
    public double gasLeft()
    {
        // this is an accessor method for the gas in the tank
        return gas;
    }
}