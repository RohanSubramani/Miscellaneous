/**
*
* This class represents an employee record. 
* It stores there name, job tilte, and salary. It
* provides a method for increasing the salary.
* 
* PLEASE MAKE SURE THIS WORKS WITH the TestExample class
*
* 
* @author: <your name here>
* @date: <the date here>
*
*/

public class Employee{
    
    // declare your instance variables here
    private String name;
    private String title;
    private double salary;
    
    // write your constructor here
    public Employee(String n, String t, double s)
    {
        name = n;
        title = t;
        salary = s;
    }
    
    // write the getName method here
    public String getName() // String is return type
    {
        return name;
    }

    // write the getTitle method here
    public String getTitle() // String is return type
    {
        return title;
    }

    // write the getSalary method here
    public double getSalary()
    {
        return salary;
    }
    
    // write the raise method here
    public void raise(double byPercent)
    {
        salary = salary + (byPercent/100.0 * salary);
    }

}    

