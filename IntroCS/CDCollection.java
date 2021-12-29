//********************************************************************
//  CDCollection.java       Author: Lewis/Loftus (modified by cannon)
//
//  Represents a collection of compact discs.
//********************************************************************

import java.text.NumberFormat;
import java.util.Locale;
import java.util.ArrayList;
import java.util.Collections;

public class CDCollection
{
    private ArrayList<CD> collection;
    private double totalCost;
    private ArrayList<String> badArtists;

    //-----------------------------------------------------------------
    //  Constructor: Creates an initially empty collection.
    //-----------------------------------------------------------------
    public CDCollection ()
    {
        collection = new ArrayList<CD>();
        totalCost = 0.0;
        badArtists = new ArrayList<String>();
    }

    //-----------------------------------------------------------------
    //  Adds a CD to the collection
    //-----------------------------------------------------------------
    public void addCD (String title, String artist, double cost, int tracks)
    {

        if (badArtists.contains(artist))
        {
            throw new BadMusicException("Yikes! " + artist + " is terrible!");
        }
        else
        {
            collection.add( new CD (title, artist, cost, tracks));
            totalCost += cost;
        }
            
    }
    
    public void addBad(String artist)
    {
        badArtists.add(artist);
    }

    //-----------------------------------------------------------------
    //  Returns a report describing the CD collection.
    //-----------------------------------------------------------------
    public String toString()
    {
        NumberFormat fmt = NumberFormat.getCurrencyInstance(Locale.US);

        String report = "~~~~~~~~~~~~~~Wow Cool~~~~~~~~~~~~~~~~~~~~~~~\n";
        report += "My CD Collection\n\n";

        report += "Number of CDs: " + collection.size() + "\n";
        report += "Total cost: " + fmt.format(totalCost) + "\n";
        report += "Average cost: " + fmt.format(totalCost/collection.size());

        report += "\n\nCD List:\n\n";

        for (CD element : collection)
            report += element.toString() + "\n";

        return report;
    }

    public void sort()
    {	
	    Collections.sort(collection);
    } 



}
