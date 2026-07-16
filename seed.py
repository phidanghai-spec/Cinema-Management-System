import os
import datetime
import random
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

    extra_movie_specs = [
        # (title, genre, duration, rating, formats, age_rating, status,
        #  release_offset_days, end_offset_days, director, cast, description)
        ("The Dark Knight", "Action, Crime, Drama", 152, 4.9, "2D, IMAX", "C16", "now_showing", -10, 45, "Christopher Nolan", "Christian Bale, Heath Ledger, Aaron Eckhart", "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice."),
        ("Inception", "Action, Sci-Fi, Adventure", 148, 4.8, "2D, IMAX", "C13", "now_showing", -8, 40, "Christopher Nolan", "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page", "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O."),
        ("The Matrix", "Action, Sci-Fi", 136, 4.7, "2D", "C16", "now_showing", -6, 35, "Lana Wachowski, Lilly Wachowski", "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss", "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth--the life he knows is the elaborate deception of an evil cyber-intelligence."),
        ("The Lord of the Rings: The Fellowship of the Ring", "Action, Adventure, Drama", 178, 4.9, "2D, IMAX", "C13", "now_showing", -12, 50, "Peter Jackson", "Elijah Wood, Ian McKellen, Orlando Bloom", "A meek Hobbit from the Shire and eight companions set out on a journey to destroy the powerful One Ring and save Middle-earth from the Dark Lord Sauron."),
        ("Gladiator", "Action, Adventure, Drama", 155, 4.8, "2D", "C16", "now_showing", -15, 30, "Ridley Scott", "Russell Crowe, Joaquin Phoenix, Connie Nielsen", "A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery."),
        ("Titanic", "Drama, Romance", 194, 4.7, "2D, 3D", "C13", "now_showing", -20, 25, "James Cameron", "Leonardo DiCaprio, Kate Winslet, Billy Zane", "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic."),
        ("Avengers: Endgame", "Action, Adventure, Sci-Fi", 181, 4.8, "2D, 3D, IMAX", "C13", "now_showing", -5, 60, "Anthony Russo, Joe Russo", "Robert Downey Jr., Chris Evans, Mark Ruffalo", "After the devastating events of Avengers: Infinity War, the universe is in ruins. With the help of remaining allies, the Avengers assemble once more."),
        ("Spider-Man: No Way Home", "Action, Adventure, Sci-Fi", 148, 4.6, "2D, 3D", "C13", "now_showing", -3, 30, "Jon Watts", "Tom Holland, Zendaya, Benedict Cumberbatch", "With Spider-Man's identity now revealed, Peter asks Doctor Strange for help. When a spell goes wrong, dangerous foes from other worlds start to appear."),
        ("Oppenheimer", "Biography, Drama, History", 180, 4.9, "2D, IMAX", "C16", "now_showing", -7, 45, "Christopher Nolan", "Cillian Murphy, Emily Blunt, Matt Damon", "The story of American scientist J. Robert Oppenheimer and his role in the development of the atomic bomb."),
        ("Barbie", "Adventure, Comedy, Fantasy", 114, 4.4, "2D", "C13", "now_showing", -9, 35, "Greta Gerwig", "Margot Robbie, Ryan Gosling, Issa Rae", "Stereotypical Barbie experiences a full-on existential crisis and must travel to the real world in order to understand herself and discover her true purpose."),
        ("Spider-Man: Into the Spider-Verse", "Animation, Action, Adventure", 117, 4.8, "2D, 3D", "P", "now_showing", -14, 20, "Bob Persichetti, Peter Ramsey", "Shameik Moore, Jake Johnson, Hailee Steinfeld", "Teen Miles Morales becomes the Spider-Man of his universe, and must join with five spider-powered individuals from other dimensions to stop a threat for all realities."),
        ("Parasite", "Drama, Thriller", 132, 4.8, "2D", "C18", "now_showing", -11, 30, "Bong Joon Ho", "Song Kang-ho, Lee Sun-kyun, Cho Yeo-jeong", "Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy Park family and the destitute Kim clan."),
        ("Joker: Folie à Deux", "Drama, Crime, Musical", 138, 0.0, "2D, IMAX", "C18", "coming_soon", 15, 60, "Todd Phillips", "Joaquin Phoenix, Lady Gaga, Brendan Gleeson", "Secuel of Joker (2019), detailing the shared madness between Arthur Fleck and Harley Quinn."),
        ("Gladiator II", "Action, Adventure, Drama", 150, 0.0, "2D, IMAX", "C16", "coming_soon", 30, 90, "Ridley Scott", "Paul Mescal, Pedro Pascal, Denzel Washington", "Years after witnessing the death of Maximus at the hands of his uncle, Lucius is forced to enter the Colosseum after his home is conquered by the tyrannical Emperors."),
        ("Moana 2", "Animation, Adventure, Comedy", 100, 0.0, "2D, 3D", "P", "coming_soon", 45, 100, "David G. Derrick Jr.", "Auli'i Cravalho, Dwayne Johnson, Alan Tudyk", "After receiving an unexpected call from her wayfinding ancestors, Moana must journey to the far seas of Oceania and into dangerous, long-lost waters for an adventure unlike anything she's ever faced."),
        ("The Batman Part II", "Action, Crime, Drama", 160, 0.0, "2D, IMAX", "C16", "coming_soon", 60, 120, "Matt Reeves", "Robert Pattinson, Andy Serkis, Jeffrey Wright", "The sequel to Matt Reeves' gritty detective take on the Caped Crusader.")
    ]

    for idx, (title, genre, duration, rating, formats, age_rating, status,
              rel_off, end_off, director, cast, description) in enumerate(extra_movie_specs):
        movie = Movie.objects.create(
            title=title,
            description=description,
            genre=genre,
            duration=duration,
            rating=rating,
            formats=formats,
            poster_url=f"https://picsum.photos/seed/cineverse-movie-{idx + 9}/600/900",
            trailer_url=None,
            release_date=datetime.date.today() + datetime.timedelta(days=rel_off),
            end_date=datetime.date.today() + datetime.timedelta(days=end_off),
            status=status,
            age_rating=age_rating,
            director=director,
            cast=cast
        )
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

    t3 = Theater.objects.create(name="CineVerse Times City", city="Hanoi",
        address="458 Minh Khai, Hai Ba Trung District", amenities="Parking, Food Court, 4DX Hall")
    t4 = Theater.objects.create(name="CineVerse Vincom Đồng Khởi", city="Ho Chi Minh City",
        address="72 Le Thanh Ton, District 1", amenities="Parking, Rooftop Lounge, Valet")
    t5 = Theater.objects.create(name="CineVerse Crescent Mall", city="Ho Chi Minh City",
        address="101 Ton Dat Tien, District 7", amenities="Parking, Food Court, Wheelchair Access")
    t6 = Theater.objects.create(name="CineVerse Vincom Đà Nẵng", city="Da Nang",
        address="910 Ngo Quyen, Son Tra District", amenities="Parking, Ocean View Lounge")

    s1_t3 = TheaterService.create_screen(t3.id, "4DX Hall", "IMAX", 8, 10)
    s2_t3 = TheaterService.create_screen(t3.id, "Standard Room 1", "2D", 6, 10)
    s1_t4 = TheaterService.create_screen(t4.id, "Premium Hall", "3D", 6, 8)
    s2_t4 = TheaterService.create_screen(t4.id, "IMAX Hall", "IMAX", 8, 12)
    s1_t5 = TheaterService.create_screen(t5.id, "Cinema Room A", "2D", 7, 10)
    s2_t5 = TheaterService.create_screen(t5.id, "Cinema Room B", "3D", 6, 9)
    s1_t6 = TheaterService.create_screen(t6.id, "IMAX Đà Nẵng", "IMAX", 8, 10)
    s2_t6 = TheaterService.create_screen(t6.id, "Standard Hall", "2D", 6, 10)

    all_screens = [s1_t1, s2_t1, s1_t2, s2_t2, s1_t3, s2_t3,
                   s1_t4, s2_t4, s1_t5, s2_t5, s1_t6, s2_t6]
    FORMAT_MULTIPLIER = {'2D': 1.0, '3D': 1.2, 'IMAX': 1.5}
    TIME_SLOTS = [datetime.time(9, 0), datetime.time(11, 30), datetime.time(14, 0),
                  datetime.time(16, 30), datetime.time(19, 0), datetime.time(21, 30)]

    now_showing_extra = [m for m in created_movies[8:] if m.status == 'now_showing']

    screen_slot_pairs = [(s, t) for s in all_screens for t in TIME_SLOTS]
    random.Random(42).shuffle(screen_slot_pairs)

    SHOWTIMES_PER_MOVIE_PER_DAY = 3
    # Đọc TOÀN BỘ lịch đã có sẵn trong DB (kể cả lịch cứng cũ) vào 1 set để tra cứu nhanh
    existing_used = set(Showtime.objects.values_list('screen_id', 'start_time'))

    for day_offset in range(10):
        current_date = today + datetime.timedelta(days=day_offset)
        for idx, movie in enumerate(now_showing_extra):
            base = idx * SHOWTIMES_PER_MOVIE_PER_DAY
            assigned = 0
            attempt = 0
            while assigned < SHOWTIMES_PER_MOVIE_PER_DAY and attempt < len(screen_slot_pairs):
                screen, slot = screen_slot_pairs[(base + attempt) % len(screen_slot_pairs)]
                attempt += 1
                start_dt = make_dt(current_date, slot)
                key = (screen.id, start_dt)
                if key in existing_used:   # đã có phim khác chiếu giờ này rồi -> bỏ qua
                    continue
                end_dt = start_dt + datetime.timedelta(minutes=movie.duration)
                Showtime.objects.create(
                    movie=movie, screen=screen, start_time=start_dt, end_time=end_dt,
                    language="Vietnamese" if idx % 3 == 0 else "English",
                    subtitle="English" if idx % 3 == 0 else "Vietnamese",
                    price_multiplier=FORMAT_MULTIPLIER.get(screen.format, 1.0)
                )
                existing_used.add(key)   # đánh dấu đã dùng, để lần lặp sau biết
                assigned += 1
    
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
