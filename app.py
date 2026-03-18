from flask import Flask, render_template, request, redirect
import sqlite3
import os , json
from flask import make_response
from reportlab.pdfgen import canvas # type: ignore
import io

app = Flask(__name__)

# Initialize the database
def init_db():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TEXT,
        time TEXT,
        location TEXT,
        seats_available INTEGER
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER,
        user_name TEXT,
        seats_booked INTEGER,
        FOREIGN KEY (event_id) REFERENCES events (id)
    )
    """)
    # Insert sample events
    cursor.execute("DELETE FROM events")
    cursor.execute("""
    INSERT INTO events (name, date, time, location, seats_available)
    VALUES 
        ('Movie A', '2024-12-01', '18:00', 'Ciné Nerwaya', 100),
        ('Concert B', '2024-12-05', '20:00', 'Canal Olympia', 50),
        ('Play C', '2024-12-10', '19:00', 'Maison du peuple', 30)
    """)
    conn.commit()
    conn.close()

# Connect to the database (creates file if it doesn't exist)
conn = sqlite3.connect("tickets.db")
cursor = conn.cursor()

# Create the 'events' table
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT NOT NULL,
    seats_available INTEGER NOT NULL,
    total_seats INTEGER NOT NULL,
    date TEXT NOT NULL
)
""")


# Commit and close
conn.commit()
conn.close()

print("Database and table created successfully!")


    

@app.route("/ticket/<int:booking_id>")
def generate_ticket(booking_id):
    # Read the booking details
    bookings = read_bookings()
    booking = next((b for b in bookings if b["booking_id"] == booking_id), None)

    if not booking:
        return "Booking not found.", 404

    # Create an in-memory buffer to hold the PDF data
    buffer = io.BytesIO()

    # Create a PDF canvas
    pdf = canvas.Canvas(buffer)

    # Add ticket details to the PDF
    pdf.setTitle("Booking Ticket")
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(100, 750, "Your Ticket Confirmation")
    pdf.setFont("Helvetica", 12)

    # Add booking information
    pdf.drawString(100, 720, f"Booking ID: {booking['booking_id']}")
    pdf.drawString(100, 700, f"Event ID: {booking['event_id']}")
    pdf.drawString(100, 680, f"Name: {booking['user_name']}")
    pdf.drawString(100, 660, f"Seats Booked: {booking['seats_booked']}")

    # Footer
    pdf.setFont("Helvetica-Oblique", 10)
    pdf.drawString(100, 620, "Thank you for booking with us!")

    # Finalize the PDF and save it to the buffer
    pdf.showPage()
    pdf.save()

    # Return the PDF as a response
    buffer.seek(0)
    response = make_response(buffer.getvalue())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename=ticket_{booking_id}.pdf"

    return response


    # Path to the JSON file
BOOKINGS_FILE = "bookings.json"

# Read all bookings from the JSON file
def read_bookings():
    if not os.path.exists(BOOKINGS_FILE):
        return []  # Return an empty list if the file doesn't exist
    with open(BOOKINGS_FILE, "r") as file:
        return json.load(file)

# Save a new booking to the JSON file
def save_booking(booking):
    bookings = read_bookings()
    bookings.append(booking)
    with open(BOOKINGS_FILE, "w") as file:
        json.dump(bookings, file, indent=4)

# Home route: Display events
@app.route("/")
def home():
    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    events = cursor.fetchall()
    conn.close()
    return render_template("home.html", events=events)

# Booking route
@app.route("/book/<int:event_id>", methods=["GET", "POST"])
def book(event_id):
    if request.method == "POST":
        user_name = request.form["user_name"]
        seats = int(request.form["seats"])
        
        conn = sqlite3.connect("tickets.db")
        cursor = conn.cursor()
        
        # Check available seats
        cursor.execute("SELECT seats_available FROM events WHERE id = ?", (event_id,))
        seats_available = cursor.fetchone()[0]
        
        if seats > seats_available:
            conn.close()
            return "Not enough seats available. Please try again."
        
        # Update event seats and add booking
        cursor.execute("UPDATE events SET seats_available = seats_available - ? WHERE id = ?", (seats, event_id))
        cursor.execute("INSERT INTO bookings (event_id, user_name, seats_booked) VALUES (?, ?, ?)", (event_id, user_name, seats))
        conn.commit()
        conn.close()
        booking_data = {
            "booking_id": len(read_bookings()) + 1,  # Auto-increment booking ID
            "event_id": event_id,
            "user_name": user_name,
            "seats_booked": seats
        }
        save_booking(booking_data)
        return f"Booking successful! <a href='/ticket/{len(read_bookings())}'>Download your ticket</a>"


    
    

    conn = sqlite3.connect("tickets.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    conn.close()
    return render_template("book.html", event=event)

if __name__ == "__main__":
    init_db()  # Initialize the database
    app.run(debug=True)


