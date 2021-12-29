/**
 * 
 * Methods of this class allow for shuffling and dealing a deck of cards.
 * 
 * @author: Rohan Subramani
 * @date: 3/23/2021
 */

public class Deck {
	
    private Card[] cards;
    private int top; //the index of the top of the deck
	
    public Deck(){
        top = 0;
        cards = new Card[52];
        int i = 0;
        for (int suit = 1; suit<=4; suit++)
        {
            for (int rank = 2; rank<=14;rank++)
            {
                cards[i] = new Card(suit,rank);
                i++;
            }
        }
    }
	
    private void swap()
    {
        // swap two random cards 
        int a = (int) (Math.random()*52);
        int b = (int) (Math.random()*52);
        Card c = cards[a];
        cards[a] = cards[b];
        cards[b] = c;
    }
    
    public void shuffle(){
        // swap two random cards 1000 times
        for (int i = 0; i < 1000; i++)
        {
            swap();
        }
        top = 0;
    }
    
    public Card deal(){
        // deal one card
        top++;
        return cards[top-1];
    }
}
