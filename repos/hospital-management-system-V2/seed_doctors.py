import uuid
import random
import csv
import os
from werkzeug.security import generate_password_hash

from backend.models import db, User, Doctor, Department


def populate_doctors():
    """
    Seed exactly ONE doctor per department (if missing),
    create corresponding User accounts,
    and export the new credentials to instance/seed_outputs/doctors.csv.

    Safe to re-run:
      - If a department already has at least one doctor, it is skipped.
      - Only newly created doctors are written to the CSV.
    """

    department_names = [
        "Cardiology", "Neurology", "Orthopedics", "Emergency", "ICU",
        "Pediatrics", "Radiology", "Oncology", "Gynecology", "Dermatology",
        "Ophthalmology", "ENT", "Psychiatry", "Physiotherapy", "Pathology",
        "Nephrology", "Urology", "Gastroenterology", "Pulmonology",
        "Cardiothoracic Surgery",
    ]

    departments = Department.query.filter(
        Department.name.in_(department_names)
    ).all()
    dept_map = {d.name: d for d in departments}

    if len(departments) != len(department_names):
        print("Some departments were not found in the database.")
        print("   Found:", [d.name for d in departments])

    first_names = [
        "Aarav", "Vihaan", "Aditya", "Arjun", "Ishaan", "Reyansh",
        "Ananya", "Diya", "Isha", "Kavya", "Riya", "Saanvi",
        "Rahul", "Neha", "Karan", "Priya", "Siddharth", "Meera",
    ]

    last_names = [
        "Sharma", "Verma", "Gupta", "Iyer", "Menon", "Patel",
        "Reddy", "Naidu", "Mukherjee", "Chatterjee", "Nair",
        "Desai", "Rao", "Kulkarni", "Bhat", "Singh", "Kaur",
    ]

    # WARNING: This is a plaintext seed password for development only.
    # In production, require doctors to change their password on first login.
    # TODO: [L53] Read seed password from env var instead of hardcoding
    default_password = "DoctorPass123"
    hashed_pw = generate_password_hash(default_password)

    created_rows = []  # rows to write to CSV

    for idx, dept_name in enumerate(department_names):
        department = dept_map.get(dept_name)
        if not department:
            print(f"⏭️  Skipping {dept_name} (department not found in DB)")
            continue


        existing_doc = Doctor.query.filter_by(department_id=department.id).first()
        if existing_doc:
            print(f"⏭️  Skipping {dept_name}: doctor already exists ({existing_doc.name}).")
            continue


        first = random.choice(first_names)
        last = random.choice(last_names)
        full_name = f"Dr. {first} {last}"


        spec_slug = dept_name.lower().replace(" ", "").replace("-", "")
        base_username = f"dr.{first.lower()}.{spec_slug}"
        username = base_username
        suffix = 1

        while User.query.filter_by(username=username).first():
            username = f"{base_username}{suffix}"
            suffix += 1


        email = f"{username.replace('dr.', '')}@hms.com"

        phone = f"9{idx:02d}{random.randint(1000000, 9999999)}"


        user = User(
            id=str(uuid.uuid4()),
            username=username,
            password=hashed_pw,
            role="doctor",
        )
        db.session.add(user)


        doctor = Doctor(
            id=str(uuid.uuid4()),
            uuid=user.id,                 
            name=full_name,
            specialization=dept_name,
            email=email,
            phone=phone,
            department_id=department.id,
            experience=random.randint(3, 20),
            rating=round(random.uniform(4.0, 4.9), 1),
        )
        db.session.add(doctor)

        # For CSV export
        created_rows.append([full_name, username, default_password, dept_name])

        print(f"✅ Created {full_name} ({username}) for {dept_name}")

    if not created_rows:
        print("ℹ️  No new doctors created. All departments already have doctors.")
        return

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("❌ Error during commit, rolled back. Error:", e)
        return

    output_dir = os.path.join("instance", "seed_outputs")
    os.makedirs(output_dir, exist_ok=True)

    csv_path = os.path.join(output_dir, "doctors.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Doctor Name", "Username", "Password", "Department"])
        writer.writerows(created_rows)

    print(f"Credentials exported to: {csv_path}")
