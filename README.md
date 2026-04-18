# DYP-UT Election Portal 🗳️

A professional, secure, and fully responsive online voting system designed for college elections. This portal features a permanent **Modern Dark Theme** and allows students to vote for their preferred candidates, while administrators manage the entire election process from a central dashboard.

## ✨ Features

- **🏆 President & Vice President**: Automatically ranks candidates and declares winners based on vote counts.
- **🌙 Permanent Dark Theme**: High-contrast, eye-friendly interface designed for modern aesthetics.
- **📱 Fully Responsive**: Optimized for seamless use on Mobile, Tablet, and Desktop devices.
- **🖼️ Candidate Management**: Administrators can add candidates with photos and manage their details.
- **🛡️ Secure Verification**: Student login requires matching PRN, Full Name, Mobile, and Mother's Name against an uploaded dataset.
- **📊 Admin Dashboard**:
    - **Election Control**: Start, stop, and reset elections with one click.
    - **Dataset Management**: Upload student lists via CSV and delete datasets by class.
    - **Real-time Analytics**: Live vote tracking with percentage progress bars.
    - **Results Export**: Print results to PDF or export to CSV.

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3 (Bootstrap 5, Animate.css, Font Awesome 6)
- **Backend**: Python (Flask)
- **Database**: SQLite (SQLAlchemy ORM)
- **Server**: Gunicorn (for production hosting)

## 🚀 Local Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/dyp-ut-election-portal.git
   cd dyp-ut-election-portal
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   - For Development: `python app.py`
   - For Production (One-click server): `python server.py`

4. **Access the Portal**:
   Go to `http://127.0.0.1:5000` in your browser.

## ☁️ Hosting Instructions

**IMPORTANT**: This is a Python/Flask application. It **cannot** be hosted on Netlify (Static Site). Use a platform that supports Python like **Render** or **Vercel**.

### **Option 1: Vercel (Recommended)**
1. Install Vercel CLI: `npm install -g vercel`
2. Run `vercel` in the project root.
3. **Database Note**: Vercel is serverless and read-only. SQLite (`voting.db`) will NOT work. You must use a cloud database like **Neon (PostgreSQL)** and set the `DATABASE_URL` environment variable in Vercel settings.

### **Option 2: Render.com**
1. **Build Command**: `pip install -r requirements.txt`
2. **Start Command**: `gunicorn app:app`
3. **Runtime**: `Python 3`
4. **Files Included**: `Procfile` and `runtime.txt` are already prepared in the repository.

## 🔑 Access Credentials

### **1. Admin Portal**
- **Route**: `/admin/login`
- **Username (PRN)**: `admin`
- **Password**: `admin123`

### **2. Student Portal**
- **Route**: `/student/login`
- **Verification**: Students must provide details exactly as they appear in the uploaded CSV dataset (PRN, Name, Mobile, Mother's Name).

## 📂 Project Structure

- `app.py`: Core Flask application with routes and database logic.
- `templates/`:
    - `index.html`: Main home page and Master template.
    - `admin.html`: Full-featured administrative dashboard.
    - `student_login.html`: Verification portal for students.
    - `vote.html`: Secure voting interface.
    - `results.html`: Live and final election results.
- `static/uploads/`: Directory for candidate photos and background images.
- `Procfile` & `runtime.txt`: Configuration for cloud hosting.
