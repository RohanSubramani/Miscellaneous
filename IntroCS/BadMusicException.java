/* ***********************************
 *                                   *
 *  This exception class should be   *
 *  instantiated and thrown when     *
 *  someone attempts to add bad      *
 *  to a CDCollection object.        *
 * **********************************/



public class BadMusicException extends IllegalArgumentException{

    public BadMusicException(){
	    super();
    }
    
    public BadMusicException(String message){
        super(message);
    }

}
