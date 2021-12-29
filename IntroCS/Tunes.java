//********************************************************************
//  Tunes.java       Author: Lewis/Loftus (modified by cannon)
//
//  Demonstrates the use of an array of objects.
//********************************************************************

public class Tunes
{
   //-----------------------------------------------------------------
   //  Creates a CDCollection object and adds some CDs to it. Prints
   //  reports on the status of the collection.
   //-----------------------------------------------------------------
   public static void main (String[] args)
   {

        CDCollection music = new CDCollection ();
      
	    try
        {
            
          
            music.addBad("Nickelback");
            music.addBad("Robert Palmer");
            music.addCD ("Storm Front", "Billy Joel", 14.95, 10);
            music.addCD ("Discipline", "King Crimson", 19.99, 26);
            music.addCD ("Greatest Hits", "Jimmy Buffet", 15.95, 13);
            music.addCD ("Trite Garbage   ", "Nickelback", 15.00, 5);
            music.addCD ("Come On Over", "Shania Twain", 1.95, 16);
        }
        catch (BadMusicException e)
        {
            System.out.println(e);
        }
        finally
        {
            System.out.println(music);
        }
   }
}
