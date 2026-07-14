import os
import datetime
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cinema_project.settings')
django.setup()

from django.utils import timezone
from cinema.models import User, Movie, Theater, Screen, Seat, Showtime, Discount, Address, Review, Combo
from cinema.services import TheaterService

def make_dt(d, t):
    return timezone.make_aware(datetime.datetime.combine(d, t))


def seed_database():
    print("Seeding CineVerse Database...")

    # 1. Clean existing records to prevent duplicates
    User.objects.all().delete()
    Movie.objects.all().delete()
    Theater.objects.all().delete()
    Showtime.objects.all().delete()
    Discount.objects.all().delete()
    Combo.objects.all().delete()


    # 2. Create Users
    admin = User.objects.create(
        email="admin@cinema.com",
        name="System Admin",
        tier="Platinum",
        points=1200,
        status="active",
        role="admin"
    )
    admin.set_password("admin123")
    admin.save()
    print("Created Admin Account: admin@cinema.com / admin123")

    customer = User.objects.create(
        email="customer@cinema.com",
        name="Alex Mercer",
        tier="Gold",
        points=340,
        status="active",
        role="customer"
    )
    customer.set_password("customer123")
    customer.save()
    print("Created Customer Account: customer@cinema.com / customer123")

    Address.objects.create(
        user=customer,
        city="Hanoi",
        district="Cau Giay",
        address="15 Duy Tan St",
        is_default=True
    )

    # 3. Create Discounts
    Discount.objects.create(
        code="SUMMER2026",
        type="percentage",
        value=20, # 20%
        min_amount=100000,
        valid_from=datetime.date.today() - datetime.timedelta(days=5),
        valid_to=datetime.date.today() + datetime.timedelta(days=60),
        usage_limit=1000,
        per_user_limit=1
    )
    Discount.objects.create(
        code="VIP100K",
        type="fixed",
        value=100000, # 100k VND
        min_amount=250000,
        valid_from=datetime.date.today() - datetime.timedelta(days=1),
        valid_to=datetime.date.today() + datetime.timedelta(days=30),
        usage_limit=500,
        per_user_limit=1
    )
    print("Created vouchers: SUMMER2026, VIP100K")

    # 4. Create Movies with high-quality poster images from Unsplash
    movies = [
        {
            "title": "Inside Out 2",
            "description": "Teenager Riley's mind headquarters is undergoing a sudden demolition to make room for something entirely unexpected: new Emotions! Joy, Sadness, Anger, Fear and Disgust aren't sure how to feel when Anxiety shows up.",
            "genre": "Animation, Family, Comedy",
            "duration": 96,
            "rating": 4.8,
            "formats": "2D, 3D",
            "poster_url": "https://images.unsplash.com/photo-1608889175123-8ec330b86f84?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/LEjhY15eCx0",
            "release_date": datetime.date.today() - datetime.timedelta(days=10),
            "end_date": datetime.date.today() + datetime.timedelta(days=30),
            "status": "now_showing",
            "age_rating": "P",
            "director": "Kelsey Mann",
            "cast": "Amy Poehler, Phyllis Smith, Lewis Black, Tony Hale"
        },
        {
            "title": "Deadpool & Wolverine",
            "description": "A listless Wade Wilson toils in civilian life. His days as the morally flexible mercenary, Deadpool, behind him. But when his homeworld faces an existential threat, Wade must reluctantly suit-up again with an even more reluctant Wolverine.",
            "genre": "Action, Sci-Fi, Comedy",
            "duration": 127,
            "rating": 4.7,
            "formats": "2D, IMAX",
            "poster_url": "https://images.unsplash.com/photo-1635805737707-575885ab0820?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/73_1biulkYk",
            "release_date": datetime.date.today() - datetime.timedelta(days=5),
            "end_date": datetime.date.today() + datetime.timedelta(days=25),
            "status": "now_showing",
            "age_rating": "C18",
            "director": "Shawn Levy",
            "cast": "Ryan Reynolds, Hugh Jackman, Emma Corrin, Morena Baccarin"
        },
        {
            "title": "Interstellar",
            "description": "In Earth's future, a global crop blight and second Dust Bowl are slowly rendering the planet uninhabitable. Professor Brand, a brilliant NASA physicist, is working on plans to save mankind by transporting Earth's population to a new home.",
            "genre": "Sci-Fi, Adventure, Drama",
            "duration": 169,
            "rating": 4.9,
            "formats": "2D, IMAX",
            "poster_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/zSWdZAWr3Tk",
            "release_date": datetime.date.today() - datetime.timedelta(days=1),
            "end_date": datetime.date.today() + datetime.timedelta(days=60),
            "status": "now_showing",
            "age_rating": "C13",
            "director": "Christopher Nolan",
            "cast": "Matthew McConaughey, Anne Hathaway, Jessica Chastain, Bill Irwin"
        },
        {
            "title": "Dune: Part Two",
            "description": "Paul Atreides unites with Chani and the Fremen while seeking revenge against the conspirators who destroyed his family. Facing a choice between the love of his life and the fate of the universe, he endeavors to prevent a terrible future only he can foresee.",
            "genre": "Sci-Fi, Action, Adventure",
            "duration": 166,
            "rating": 4.9,
            "formats": "2D, IMAX",
            "poster_url": "https://images.unsplash.com/photo-1547483238-2cbf88bc1463?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/Way9Dexny3w",
            "release_date": datetime.date.today() - datetime.timedelta(days=15),
            "end_date": datetime.date.today() + datetime.timedelta(days=45),
            "status": "now_showing",
            "age_rating": "C16",
            "director": "Denis Villeneuve",
            "cast": "Timothée Chalamet, Zendaya, Rebecca Ferguson, Javier Bardem"
        },
        {
            "title": "Despicable Me 4",
            "description": "Gru, Lucy, Margo, Edith, and Agnes welcome a new member to the family, Gru Jr., who is intent on tormenting his dad. Gru faces a new nemesis in Maxime Le Mal and his femme fatale girlfriend Valentina, and the family is forced to go on the run.",
            "genre": "Animation, Family, Comedy",
            "duration": 94,
            "rating": 4.5,
            "formats": "2D, 3D",
            "poster_url": "https://images.unsplash.com/photo-1501430654243-c934ccd2c190?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/qQuxc7sDFQ0",
            "release_date": datetime.date.today() - datetime.timedelta(days=2),
            "end_date": datetime.date.today() + datetime.timedelta(days=40),
            "status": "now_showing",
            "age_rating": "P",
            "director": "Chris Renaud",
            "cast": "Steve Carell, Kristen Wiig, Will Ferrell, Sofía Vergara"
        },
        {
            "title": "A Quiet Place: Day One",
            "description": "Experience the day the world went silent in this thriller following a young woman navigating the initial, terrifying invasion of sound-sensitive alien creatures in New York City.",
            "genre": "Horror, Thriller, Sci-Fi",
            "duration": 100,
            "rating": 4.2,
            "formats": "2D",
            "poster_url": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/YPY7J-flzE8",
            "release_date": datetime.date.today() + datetime.timedelta(days=10),
            "end_date": datetime.date.today() + datetime.timedelta(days=40),
            "status": "coming_soon",
            "age_rating": "C16",
            "director": "Michael Sarnoski",
            "cast": "Lupita Nyong'o, Joseph Quinn, Alex Wolff, Djimon Hounsou"
        },
        {
            "title": "Avatar: Fire and Ash",
            "description": "The third installment of James Cameron's science-fiction franchise. Lo'ak and Tsireya traverse across Pandora to discover the Ash People, a hostile clan of Na'vi who reside near volcanic regions.",
            "genre": "Sci-Fi, Adventure, Action",
            "duration": 160,
            "rating": 0.0,
            "formats": "3D, IMAX",
            "poster_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/8v_T75w3jUY",
            "release_date": datetime.date.today() + datetime.timedelta(days=120),
            "end_date": datetime.date.today() + datetime.timedelta(days=160),
            "status": "coming_soon",
            "age_rating": "C13",
            "director": "James Cameron",
            "cast": "Sam Worthington, Zoe Saldana, Sigourney Weaver, Stephen Lang"
        },
        {
            "title": "Wicked",
            "description": "The story of how a green-skinned woman framed by the Wizard of Oz becomes the Wicked Witch of the West; Elphaba Cobb and Glinda Upland navigate wizardry school, their contrasting lives, and their unlikely friendship.",
            "genre": "Fantasy, Musical, Drama",
            "duration": 140,
            "rating": 0.0,
            "formats": "2D, IMAX",
            "poster_url": "https://images.unsplash.com/photo-1519074069444-1ba4e66640c2?q=80&w=600&auto=format&fit=cover",
            "trailer_url": "https://www.youtube.com/embed/6COmYeLsz4c",
            "release_date": datetime.date.today() + datetime.timedelta(days=15),
            "end_date": datetime.date.today() + datetime.timedelta(days=50),
            "status": "coming_soon",
            "age_rating": "P",
            "director": "Jon M. Chu",
            "cast": "Cynthia Erivo, Ariana Grande, Michelle Yeoh, Jeff Goldblum"
        }
    ]

    created_movies = []
    for m_data in movies:
        movie = Movie.objects.create(**m_data)
        created_movies.append(movie)
        print(f"Added Movie: {movie.title} ({movie.status})")

    # Write a default review for Interstellar
    Review.objects.create(
        user=customer,
        movie=created_movies[2], # Interstellar
        rating=5,
        comment="Absolutely mind-blowing cinematic masterpiece! The soundtrack by Hans Zimmer is legendary."
    )

    # 5. Create Theaters & Screens using TheaterService to auto-generate seat maps
    t1 = Theater.objects.create(
        name="CineVerse Royal City",
        city="Hanoi",
        address="B2 Floor, Vincom Royal City, Thanh Xuan District",
        amenities="Parking, Food Court, VIP Lounge, Kids Playroom"
    )
    t2 = Theater.objects.create(
        name="CineVerse Landmark 72",
        city="Hanoi",
        address="Keangnam Landmark 72, Cau Giay District",
        amenities="Parking, Executive Dining, Wheelchair Access"
    )

    print("Created Theaters: CineVerse Royal City & CineVerse Landmark 72")

    # Generate screens & auto-create seat layout grids (rows x cols)
    # Screen 1: IMAX, 8 rows, 10 columns = 80 seats
    s1_t1 = TheaterService.create_screen(t1.id, "IMAX Hall 1", "IMAX", 8, 10)
    # Screen 2: Standard, 6 rows, 10 columns = 60 seats
    s2_t1 = TheaterService.create_screen(t1.id, "Cinema Room 2", "2D", 6, 10)

    s1_t2 = TheaterService.create_screen(t2.id, "VIP Hall 1", "3D", 5, 8)
    s2_t2 = TheaterService.create_screen(t2.id, "IMAX Hall 2", "IMAX", 8, 10)
    print("Auto-generated layouts and seat grids for Screens.")

    # 6. Create Showtimes (For the next 7 days)
    today = datetime.datetime.now().date()
    print("Generating showtimes for the next 7 days...")
    
    for day_offset in range(7):
        current_date = today + datetime.timedelta(days=day_offset)
        
        # Inside Out 2
        Showtime.objects.create(
            movie=created_movies[0],
            screen=s1_t1,
            start_time=make_dt(current_date, datetime.time(10, 0)),
            end_time=make_dt(current_date, datetime.time(11, 36)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.2
        )
        Showtime.objects.create(
            movie=created_movies[0],
            screen=s2_t1,
            start_time=make_dt(current_date, datetime.time(14, 0)),
            end_time=make_dt(current_date, datetime.time(15, 36)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.0
        )
        
        # Deadpool & Wolverine
        Showtime.objects.create(
            movie=created_movies[1],
            screen=s2_t1,
            start_time=make_dt(current_date, datetime.time(17, 0)),
            end_time=make_dt(current_date, datetime.time(19, 7)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.0
        )
        Showtime.objects.create(
            movie=created_movies[1],
            screen=s1_t1,
            start_time=make_dt(current_date, datetime.time(20, 30)),
            end_time=make_dt(current_date, datetime.time(22, 37)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.2
        )
        
        # Interstellar
        Showtime.objects.create(
            movie=created_movies[2],
            screen=s2_t2,
            start_time=make_dt(current_date, datetime.time(19, 30)),
            end_time=make_dt(current_date, datetime.time(22, 19)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.3
        )
        Showtime.objects.create(
            movie=created_movies[2],
            screen=s1_t2,
            start_time=make_dt(current_date, datetime.time(13, 0)),
            end_time=make_dt(current_date, datetime.time(15, 49)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.5
        )
        
        # Dune: Part Two
        Showtime.objects.create(
            movie=created_movies[3],
            screen=s1_t2,
            start_time=make_dt(current_date, datetime.time(19, 0)),
            end_time=make_dt(current_date, datetime.time(21, 46)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.5
        )
        Showtime.objects.create(
            movie=created_movies[3],
            screen=s2_t2,
            start_time=make_dt(current_date, datetime.time(10, 30)),
            end_time=make_dt(current_date, datetime.time(13, 16)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.3
        )
        
        # Despicable Me 4
        Showtime.objects.create(
            movie=created_movies[4],
            screen=s2_t1,
            start_time=make_dt(current_date, datetime.time(11, 45)),
            end_time=make_dt(current_date, datetime.time(13, 19)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.0
        )
        Showtime.objects.create(
            movie=created_movies[4],
            screen=s1_t1,
            start_time=make_dt(current_date, datetime.time(15, 0)),
            end_time=make_dt(current_date, datetime.time(16, 34)),
            language="English",
            subtitle="Vietnamese",
            price_multiplier=1.2
        )

        
    print("Created Active Showtimes for the next 7 days.")
    
    # 8. Create Combos
    Combo.objects.create(
        name="Combo Solo",
        description="1 Bắp Ngọt Vừa + 1 Nước Ngọt (Medium)",
        price=75000
    )
    Combo.objects.create(
        name="Combo Đôi",
        description="1 Bắp Lớn + 2 Nước Ngọt (Medium)",
        price=105000
    )
    Combo.objects.create(
        name="Combo Gia Đình",
        description="2 Bắp Ngọt Vừa + 3 Nước Ngọt (Medium)",
        price=155000
    )
    Combo.objects.create(
        name="Combo Siêu Cấp VIP",
        description="1 Bắp Lớn Đặc Biệt + 2 Nước Ngọt Lớn + 1 Khoai Tây Chiên",
        price=135000
    )
    print("Created food & drinks combos.")

    print("Database seeding completed successfully! Ready for launch.")


if __name__ == '__main__':
    seed_database()
