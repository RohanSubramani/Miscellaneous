class Participant:
    """
    A class to represent a participant in the study.
    
    Attributes:
        name (str): The name of the participant
        starting_location (str): The starting location of the participant
        gender (str): The gender of the participant
        prior_experience_rating (int/float): Rating of the participant's prior experience
    """
    
    def __init__(self, name, starting_location, gender, prior_experience_rating):
        """
        Initialize a Participant instance.
        
        Args:
            name (str): The name of the participant
            starting_location (str): The starting location of the participant
            gender (str): The gender of the participant
            prior_experience_rating (int/float): Rating of the participant's prior experience
        """
        self.name = name
        self.starting_location = starting_location
        self.gender = gender
        self.prior_experience_rating = prior_experience_rating
    
    def __repr__(self):
        """Return a string representation of the Participant."""
        return (f"Participant(name='{self.name}', "
                f"starting_location='{self.starting_location}', "
                f"gender='{self.gender}', "
                f"prior_experience_rating={self.prior_experience_rating})")
    
    def __str__(self):
        """Return a human-readable string representation of the Participant."""
        return (f"{self.name} from {self.starting_location}, "
                f"Gender: {self.gender}, "
                f"Prior Experience: {self.prior_experience_rating}")


class Apartment:
    """
    A class to represent an apartment with participants.
    
    Attributes:
        participants (list): List of Participant objects living in the apartment
        number_of_bedrooms (int): Number of bedrooms in the apartment
        number_of_bathrooms (int): Number of bathrooms in the apartment
    """
    
    def __init__(self, number_of_bedrooms, number_of_bathrooms, participants=None):
        """
        Initialize an Apartment instance.
        
        Args:
            number_of_bedrooms (int): Number of bedrooms in the apartment
            number_of_bathrooms (int): Number of bathrooms in the apartment
            participants (list, optional): List of Participant objects. Defaults to empty list.
        
        Raises:
            ValueError: If number of participants exceeds number of bedrooms
        """
        self.number_of_bedrooms = number_of_bedrooms
        self.number_of_bathrooms = number_of_bathrooms
        self.participants = participants if participants is not None else []
        
        # Enforce bedroom constraint
        if len(self.participants) > self.number_of_bedrooms:
            raise ValueError(
                f"Number of participants ({len(self.participants)}) cannot exceed "
                f"number of bedrooms ({self.number_of_bedrooms})"
            )
    
    def add_participant(self, participant):
        """
        Add a participant to the apartment.
        
        Args:
            participant (Participant): The participant to add
        
        Raises:
            ValueError: If adding the participant would exceed bedroom capacity
        """
        if len(self.participants) >= self.number_of_bedrooms:
            raise ValueError(
                f"Cannot add participant: apartment already has {len(self.participants)} "
                f"participants and only {self.number_of_bedrooms} bedrooms"
            )
        self.participants.append(participant)
    
    def __repr__(self):
        """Return a string representation of the Apartment."""
        return (f"Apartment(bedrooms={self.number_of_bedrooms}, "
                f"bathrooms={self.number_of_bathrooms}, "
                f"participants={len(self.participants)})")
    
    def __str__(self):
        """Return a human-readable string representation of the Apartment."""
        return (f"Apartment: {self.number_of_bedrooms} bed, {self.number_of_bathrooms} bath, "
                f"{len(self.participants)} participants")


class Building:
    """
    A class to represent a building containing apartments.
    
    Attributes:
        apartments (list): List of Apartment objects in the building
    """
    
    def __init__(self, apartments=None):
        """
        Initialize a Building instance.
        
        Args:
            apartments (list, optional): List of Apartment objects. Defaults to empty list.
        """
        self.apartments = apartments if apartments is not None else []
    
    def add_apartment(self, apartment):
        """
        Add an apartment to the building.
        
        Args:
            apartment (Apartment): The apartment to add
        """
        self.apartments.append(apartment)
    
    def total_participants(self):
        """Return the total number of participants in the building."""
        return sum(len(apt.participants) for apt in self.apartments)
    
    def __repr__(self):
        """Return a string representation of the Building."""
        return f"Building(apartments={len(self.apartments)})"
    
    def __str__(self):
        """Return a human-readable string representation of the Building."""
        return (f"Building with {len(self.apartments)} apartments, "
                f"{self.total_participants()} total participants")


# Example usage with placeholder values
if __name__ == "__main__":
    # Create some participants
    participant1 = Participant("Alice Johnson", "New York", "Female", 8)
    participant2 = Participant("Bob Smith", "Los Angeles", "Male", 5)
    participant3 = Participant("Jordan Lee", "Chicago", "Non-binary", 7)
    participant4 = Participant("Diana Martinez", "Boston", "Female", 9)
    participant5 = Participant("Eric Chen", "Seattle", "Male", 6)
    
    # Create apartments with participants
    # Apartment 1: 2 bedrooms, 1 bathroom, 2 participants
    apt1 = Apartment(
        number_of_bedrooms=2,
        number_of_bathrooms=1,
        participants=[participant1, participant2]
    )
    
    # Apartment 2: 3 bedrooms, 2 bathrooms, 2 participants
    apt2 = Apartment(
        number_of_bedrooms=3,
        number_of_bathrooms=2,
        participants=[participant3, participant4]
    )
    
    # Apartment 3: 1 bedroom, 1 bathroom, 1 participant
    apt3 = Apartment(
        number_of_bedrooms=1,
        number_of_bathrooms=1,
        participants=[participant5]
    )
    
    # Create a building with the apartments
    building = Building(apartments=[apt1, apt2, apt3])
    
    # Display information
    print(building)
    print("\nApartments in building:")
    for i, apt in enumerate(building.apartments, 1):
        print(f"\n  Apartment {i}: {apt}")
        for j, participant in enumerate(apt.participants, 1):
            print(f"    Participant {j}: {participant}")

