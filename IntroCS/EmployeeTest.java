/**
*
* This class is meant to test the Employee class. 
* You must write this one!
* 
* @author: <your name here>
* @date: <the date here>
*
*/

import java.util.Scanner; // you'll need this to use a Scanner

public class EmployeeTest{
    
    public static void main(String[] args){
    
    // Make Scanner
    Scanner scan = new Scanner(System.in);
    // Get name
    System.out.println("What's the name? ");
    String name = scan.nextLine(); // NOT THE SAME name

    // Get title
    System.out.println("What's the title? ");
    String title = scan.nextLine(); // NOT THE SAME title
        
    // Get salary
    System.out.println("What's the salary? ");
    double salary = scan.nextDouble(); // NOT THE SAME salary
    
    Employee myEmployee = new Employee(name,title,salary);    
        
    System.out.println("The employee's name is " + myEmployee.getName() + ".");
    System.out.println("The employee's title is " + myEmployee.getTitle() + ".");
    System.out.println("The employee's salary is $" + myEmployee.getSalary() + ".");
    
    System.out.println("I hear the employee is getting a raise! What percent is the raise? ");
    double percent = scan.nextDouble();
    myEmployee.raise(percent);
    System.out.println("The new salary is $" + myEmployee.getSalary() + ".");    
    }    // end main
}    // end class

