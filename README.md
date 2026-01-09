# 📅 Timetable Optimizer System

A comprehensive web-based application designed to streamline the creation, management, and visualization of university class schedules. Built with **Python (Flask)**, this system helps administrators optimize time slots, avoid conflicts, and manage staff workloads effectively.

## ✨ Key Features

*   **📊 Interactive Dashboard:**
    *   Visual analytics using **Chart.js** to show class distribution by department and staff workload.
    *   Quick navigation to key administrative tasks.
*   **🗓️ Dynamic Timetable Views:**
    *   **Department Wise:** View schedules filtered by Department, Year, and Semester.
    *   **Staff Wise:** Track individual faculty schedules.
    *   **Visual Grid:** Clear weekly grid view with automatic indicators for Breaks and Lunch.
*   **✅ Smart Slot Management:**
    *   **Check Slots:** Instantly verify if a specific time slot is free or occupied for a staff member or department.
    *   **Conflict Prevention:** Visual cues (Red/Green) to prevent double-booking.
    *   **Auto Assign:** Feature to automatically suggest or assign subjects to free slots.
*   **📥 Export Capabilities:**
    *   Download timetables as **Excel** spreadsheets.
    *   Generate printable **PDF** versions of the schedule.
*   **🛠️ Management Tools:**
    *   Secure **Login** system.
    *   Full **CRUD** (Create, Read, Update, Delete) capabilities for timetable entries.

## 💻 Tech Stack

*   **Backend:** Python (Flask Framework)
*   **Frontend:** HTML5, CSS3, JavaScript
*   **Visualization:** Chart.js
*   **Templating Engine:** Jinja2

## 🚀 Getting Started

Follow these steps to set up the project locally.

### Prerequisites
*   Python 3.x installed on your machine.

### Installation

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/yourusername/timetable-optimizer.git
    cd timetable-optimizer
    ```

2.  **Set up a Virtual Environment (Recommended)**
    ```bash
    # Windows
    python -m venv venv
    venv\Scripts\activate

    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install flask pandas openpyxl
    # Note: Install other dependencies listed in your requirements.txt
    ```

4.  **Run the Application**
    ```bash
    python app.py
    ```

5.  **Access the System**
    Open your web browser and navigate to: `http://127.0.0.1:5000`

---
*Developed for efficient academic scheduling and resource management.*