/******************************************
* CreditCard.java 
* Rohan Subramani
* 
* Methods of this class determine weather a
* credit card number is valid
*
******************************************/

public class CreditCard{
    private String number;
    private boolean valid;
    private int errorCode;
    private int digit1;
    private int digit2;
    private int digit3;
    private int digit4; 
    private int digit5;
    private int digit6;
    private int digit7;
    private int digit8;
    private int digit9;
    private int digit10;
    private int digit11;
    private int digit12;
    
    // Constructor
    public CreditCard(String n)
    {
        number = n;
        valid = true;
        errorCode = 0;
        digit1 = Integer.parseInt(number.substring(0,1));
        digit2 = Integer.parseInt(number.substring(1,2));
        digit3 = Integer.parseInt(number.substring(2,3));
        digit4 = Integer.parseInt(number.substring(3,4));
        digit5 = Integer.parseInt(number.substring(5,6));
        digit6 = Integer.parseInt(number.substring(6,7));
        digit7 = Integer.parseInt(number.substring(7,8));
        digit8 = Integer.parseInt(number.substring(8,9));
        digit9 = Integer.parseInt(number.substring(10,11));
        digit10 = Integer.parseInt(number.substring(11,12));
        digit11 = Integer.parseInt(number.substring(12,13));
        digit12 = Integer.parseInt(number.substring(13,14));
    }
    
    // Methods I need: check(), isValid(), getErrorCode()
    // I can do each part of the check separately, then combine them
    
    // Check that first digit is a 4
    private void check1() 
    {
        if (digit1 != 4)
        {
            valid = false;
            if (errorCode == 0)
            {
                errorCode = 1;
            }
        }
    }
    
    // Check that 4th digit is 1 greater than 5th digit
    private void check2() 
    {
        if (digit4 != digit5 + 1)
        {
            valid = false;
            if (errorCode == 0)
            {
                errorCode = 2;
            }
        }
    }
    
    // Check that the product of digits 1, 5, and 9 is equal to 24
    private void check3() 
    {
        if (digit1 * digit5 * digit9 != 24)
        {
            valid = false;
            if (errorCode == 0)
            {
                errorCode = 3;
            }
        }
    }
    
    // Check that the sum of all digits is divisible by 4
    private void check4() 
    {
        int sum_tot = digit1 + digit2 + digit3 + digit4 + digit5 + digit6
                         + digit7 + digit8 + digit9 + digit10 + digit11 + digit12;
        if ((sum_tot/4.0)!= (sum_tot/4))
        {
            valid = false;
            if (errorCode == 0)
            {
                errorCode = 4;
            }
        }
    }
    
    // Check that the sum of the first four digits is one less than the sum of 
    // the last four digits
    private void check5() 
    {
        int sum_first4 = digit1 + digit2 + digit3 + digit4;
        int sum_last4 = digit9 + digit10 + digit11 + digit12;
        if (sum_first4 != sum_last4 - 1)
        {
            valid = false;
            if (errorCode == 0)
            {
                errorCode = 5;
            }
        }
    }
    
    // Check that if you treat the first two digits as a two-digit number, and
    // the seventh and eight digits as a two digit number, the sum is 100.
    private void check6() 
    {
        int first_two_digit = Integer.parseInt(number.substring(0,2));
        int second_two_digit = Integer.parseInt(number.substring(7,9));
        if (first_two_digit + second_two_digit != 100)
        {
            valid = false;
            if (errorCode == 0)
            {
                errorCode = 6;
            }
        }
    }
    
    public void check()
    {
        check1();
        check2();
        check3();
        check4();
        check5();
        check6();
    }
    
    public boolean isValid()
    {
        return valid;
    }
    
    public int getErrorCode()
    {
        return errorCode;
    }
}