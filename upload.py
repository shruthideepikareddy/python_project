from supabase import create_client, Client

# Replace with your actual Supabase credentials
SUPABASE_URL = "https://hlhzjdzqfwrmoultblat.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhsaHpqZHpxZndybW91bHRibGF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI0MDgxNjMsImV4cCI6MjA1Nzk4NDE2M30.xWHJh_llH7MNf-g0Dic9EXvXjzSBMSGuYc0VX0uuAEM"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ✅ Corrected Student Data (List of Dictionaries)
data = [
    {
        "registration_number": "AP23110011648",
        "name": "YellaReddy suda",
        "major": "Python",
        "starting_year": 2023,
        "total_attendance": 7,
        "standing": "G",
        "year": 2,
        "last_attendance_time": "2025-03-20 00:55:20"
    }
]

# ✅ Insert Data into Supabase
response = supabase.table("students").insert(data).execute()

# ✅ Check Response
if response.data:
    print("✅ Data inserted successfully:", response.data)
else:
    print("⚠️ Failed to insert data, Error:", response.error)
