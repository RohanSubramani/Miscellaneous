/**
 * This class allows for the creation of card objects, comparisons betweens 
 * them, and conversion of cards to strings. 
 * 
 * @author: Rohan Subramani
 * @date: 3/23/2021
 */

public class Card implements Comparable<Card>{
	
    private int suit; //use integers 1-4 to encode the suit
    private int rank; //use integers 1-13 to encode the rank
	
    public Card(int s, int r){
        suit = s;
        rank = r;
    }
	
    
    public int compareTo(Card c){
        int answer;
        if (this.rank>c.rank)
        {
            answer = 1;
        }
        else if (this.rank<c.rank)
        {
            answer = -1;
        }
        else // if (this.rank == c.rank)
        {
            if (this.suit>c.suit)
            {
                answer = 1;
            }
            else if (this.suit<c.suit)
            {
                answer = -1;
            }
            else // Not relevant in this game, but useful in other games 
            {
                answer = 0;
            }
        }
        return answer;
    }
	
    public String toString(){
        String description;
        String suitName = "";
        String rankName;
        
        if (suit == 1)
        {
            suitName = "Clubs";
        }
        else if (suit == 2)
        {
            suitName = "Diamonds";
        }
        else if (suit == 3)
        {
            suitName = "Hearts";
        }
        else if (suit == 4)
        {
            suitName = "Spades";
        }
        
        if (rank == 11)
        {
            rankName = "Jack";
        }
        else if (rank == 12)
        {
            rankName = "Queen";
        }
        else if (rank == 13)
        {
            rankName = "King";
        }
        else if (rank == 14)
        {
            rankName = "Ace";
        }
        else
        {
            rankName = String.valueOf(rank);
        }

        description = rankName + " of " + suitName;
        return description;
    }
    
    //add some more methods here if needed
    
    public int getRank()
    {
        return rank;
    }
    
    public int getSuit()
    {
        return suit;
    }

}
