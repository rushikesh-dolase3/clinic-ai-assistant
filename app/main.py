from fastapi import FastAPI, Form, HTTPException, Request   # ✅ Request add kiya
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime

from app.database import engine, Base, create_tables, SessionLocal
from app.models import Doctor, Appointment

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Session
app.add_middleware(SessionMiddleware, secret_key="supersecretkey")

# Static
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def startup():
    create_tables()


# -----------------------------
# Twilio Reply Function
# -----------------------------
def reply(message: str):
    return Response(
        content=f"<Response><Message>{message}</Message></Response>",
        media_type="application/xml"
    )


# -----------------------------
# Home
# -----------------------------
@app.get("/")
def home():
    return {"message": "Clinic AI Running 🚀"}


# -----------------------------
# Appointments API
# -----------------------------
@app.get("/appointments")
def list_appointments():
    db = SessionLocal()
    data = db.query(Appointment).all()

    result = []
    for a in data:
        result.append({
            "id": a.id,
            "patient_name": a.patient_name,
            "phone": a.phone,
            "doctor": a.doctor,
            "date": a.date,
            "time": a.time
        })

    db.close()
    return result


@app.delete("/appointments/{id}")
def delete_appointment(id: int):
    db = SessionLocal()

    appt = db.query(Appointment).filter(Appointment.id == id).first()

    if not appt:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(appt)
    db.commit()
    db.close()

    return {"message": "Deleted"}


# -----------------------------
# ADMIN LOGIN UI
# -----------------------------
@app.get("/admin", response_class=HTMLResponse)
def admin():
    return """ 
    <html>
    <head>
    <title>Admin Login</title>
    <style>
    body{
        margin:0;
        font-family:Arial;
        background:linear-gradient(135deg,#667eea,#764ba2);
        height:100vh;
        display:flex;
        justify-content:center;
        align-items:center;
    }
    .card{
        background:white;
        padding:30px;
        border-radius:12px;
        width:300px;
        box-shadow:0 10px 30px rgba(0,0,0,0.2);
        text-align:center;
    }
    input{
        width:100%;
        padding:10px;
        margin:10px 0;
        border:1px solid #ccc;
        border-radius:6px;
    }
    button{
        width:100%;
        padding:10px;
        background:#667eea;
        color:white;
        border:none;
        border-radius:6px;
        cursor:pointer;
    }
    </style>
    </head>

    <body>
        <div class="card">
            <h2>Doctor Login</h2>
            <form method="post" action="/admin-login">
                <input name="username" placeholder="Username" required>
                <input name="password" type="password" placeholder="Password" required>
                <button>Login</button>
            </form>
        </div>
    </body>
    </html>
    """


# -----------------------------
# ✅ LOGIN (SESSION ADDED)
# -----------------------------
@app.post("/admin-login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()

    username = username.strip()
    password = password.strip()

    user = db.query(Doctor).filter(
        Doctor.username == username
    ).first()

    db.close()

    if not user:
        return {"error": "User not found"}

    if user.password != password:
        return {"error": "Wrong password"}

    # ✅ SESSION SAVE
    request.session["user"] = username

    return RedirectResponse("/dashboard", status_code=303)


# -----------------------------
# CREATE ADMIN (same)
# -----------------------------
@app.get("/create-admin")
def create_admin():
    db = SessionLocal()

    admin = Doctor(
        username="admin",
        password="1234",
        name="Dr Admin"
    )

    db.add(admin)
    db.commit()
    db.close()

    return {"message": "Admin created"}    


# -----------------------------
# ✅ DASHBOARD (PROTECTED)
# -----------------------------
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):

    # ✅ PROTECTION
    if not request.session.get("user"):
        return RedirectResponse("/admin")

    return """
    <html>
    <head>
    <title>Dashboard</title>

    <style>
    body{
        font-family:Arial;
        background:#f4f6f9;
        padding:30px;
    }
    h2{
        color:#333;
    }
    .card{
        background:white;
        padding:20px;
        border-radius:10px;
        box-shadow:0 0 10px rgba(0,0,0,0.1);
    }
    .appt{
        display:flex;
        justify-content:space-between;
        padding:10px;
        border-bottom:1px solid #eee;
    }
    button{
        padding:6px 12px;
        border:none;
        background:#667eea;
        color:white;
        border-radius:6px;
        cursor:pointer;
    }
    .delete{
        background:#e53e3e;
    }
    </style>

    </head>

    <body>

    <h2>Doctor Dashboard</h2>

    <!-- ✅ LOGOUT BUTTON -->
    <a href="/logout"><button>Logout</button></a>

    <br><br>

    <button onclick="load()">Load Appointments</button>

    <div class="card" id="data"></div>

    <script>
    async function load(){
        let res = await fetch('/appointments')
        let data = await res.json()

        let html = ""

        data.forEach(a=>{
            html += `
            <div class="appt">
                <div>
                <b>${a.patient_name}</b><br>
                ${a.doctor}<br>
                ${a.date} | ${a.time}
                </div>
                <button class="delete" onclick="del(${a.id})">Delete</button>
            </div>
            `
        })

        document.getElementById("data").innerHTML = html
    }

    async function del(id){
        await fetch('/appointments/'+id,{method:'DELETE'})
        load()
    }
    </script>

    </body>
    </html>
    """


# -----------------------------
# ✅ LOGOUT
# -----------------------------
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/admin")


# -----------------------------
# WhatsApp BOT (UNCHANGED)
# -----------------------------
user_states = {}
user_data = {}

@app.post("/whatsapp")
async def whatsapp(Body: str = Form(...), From: str = Form(...)):

    msg = Body.strip().lower()

    if From not in user_states:
        user_states[From] = "start"

    state = user_states[From]

    if msg == "hi":
        user_states[From] = "menu"
        return reply("Hello 👋 Welcome to Clinic AI\nType 1 to book appointment")

    if state == "menu" and msg == "1":
        user_states[From] = "name"
        user_data[From] = {}
        return reply("Enter your name")

    if state == "name":
        user_data[From]["name"] = Body
        user_states[From] = "phone"
        return reply("Enter phone number")

    if state == "phone":
        user_data[From]["phone"] = Body
        user_states[From] = "date"
        return reply("Enter appointment date (DD/MM/YYYY)")

    if state == "date":
        try:
            datetime.strptime(Body, "%d/%m/%Y")
        except:
            return reply("❌ Enter valid date format (DD/MM/YYYY)")

        user_data[From]["date"] = Body
        user_states[From] = "doctor"

        return reply(
            "Select Doctor:\n"
            "1. Dr Sharma\n"
            "2. Dr Mehta\n"
            "3. Dr Gupta"
        )

    if state == "doctor":

        doctors = {
            "1": "Dr Sharma",
            "2": "Dr Mehta",
            "3": "Dr Gupta"
        }

        if msg not in doctors:
            return reply("Please select 1, 2 or 3")

        user_data[From]["doctor"] = doctors[msg]
        user_states[From] = "time"

        return reply(
            "Select Time:\n"
            "1. 10:00 AM\n"
            "2. 11:00 AM\n"
            "3. 12:00 PM"
        )

    if state == "time":

        slots = {
            "1": "10:00 AM",
            "2": "11:00 AM",
            "3": "12:00 PM"
        }

        if msg not in slots:
            return reply("Choose valid slot (1-3)")

        user_data[From]["time"] = slots[msg]
        data = user_data[From]

        db = SessionLocal()

        existing = db.query(Appointment).filter(
            Appointment.date == data["date"],
            Appointment.time == data["time"],
            Appointment.doctor == data["doctor"]
        ).first()

        if existing:
            db.close()
            return reply("❌ This slot is already booked. Try another time.")

        appt = Appointment(
            patient_name=data["name"],
            phone=data["phone"],
            doctor=data["doctor"],
            date=data["date"],
            time=data["time"]
        )

        db.add(appt)
        db.commit()
        db.close()

        user_states[From] = "start"

        return reply(
            f"✅ Appointment Confirmed\n\n"
            f"Name: {data['name']}\n"
            f"Doctor: {data['doctor']}\n"
            f"Date: {data['date']}\n"
            f"Time: {data['time']}"
        )

    return reply("Type 'hi' to start")