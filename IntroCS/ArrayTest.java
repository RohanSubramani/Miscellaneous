
//********************************************************************
//  DataTest.java    
//
//  Test Class for ArrayStuff
//  
//********************************************************************

public class ArrayTest{
    
    public static void main(String[] args){
        
        // make a random test array
        int[] nums=new int[6];
        for(int i=0;i<nums.length;i++){
            nums[i]= (int) (Math.random()*101);
        } 
        
        
        // make string versions of the test array
        String nums_str="";
        for(int element:nums)
            nums_str+=element+" ";
        
        
        // make string versions of the results
        String nums_ind="";
        for(int element:ArrayStuff.evenIndices(nums))
            nums_ind+=element+" ";
        
        String nums_val="";
        for(int element:ArrayStuff.evenValues(nums))
            nums_val+=element+" ";
        
        String nums_rev="";
        for(int element:ArrayStuff.reverse(nums))
            nums_rev+=element+" ";
        
        String nums_lwbf="";
        for(int element:ArrayStuff.lastWillBeFirst(nums))
            nums_lwbf+=element+" ";
       
        
       // print results
        System.out.println("starting contents: \t"+nums_str);
        System.out.println("evenIndicies produces: \t"+nums_ind);
        System.out.println("evenValues produces: \t"+nums_val);
        System.out.println("reverse produces: \t"+nums_rev);
        System.out.println("last one produces: \t"+nums_lwbf);
        
    }
       
}