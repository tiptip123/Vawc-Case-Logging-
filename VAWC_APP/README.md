# VAWC Case Management System - Barangay Tankulan

A professional and secure desktop application designed for Barangay Tankulan, Manolo Fortich, Bukidnon, to streamline the logging, management, and reporting of VAWC (Violence Against Women and Their Children) cases.

![Logo](logo/tankulan.jpg)

## 🌟 Key Features

- **Dashboard**: Real-time summary of total cases, monthly/yearly statistics, and case status distribution.
- **Case Logging**: Comprehensive record-keeping including client details, type of abuse (RA 9262), respondent info, and attachments.
- **Automatic Refresh**: Instant UI updates across all tabs whenever records are added or edited.
- **Analytics**: Visual data representation using interactive charts for better decision-making.
- **Reporting**: Export detailed case logs to professional PDF and Excel formats.
- **User Management**: Secure RBAC (Role-Based Access Control) with encrypted passwords for Admin and Staff.
- **Database Management**: Integrated backup and restoration tools for data security.
- **Fullscreen Mode**: Toggle fullscreen view using the **F8** hotkey.

## 📋 Prerequisites

- **Windows OS** (Optimized for Windows 10/11)
- **Python 3.10 or higher**

## 🚀 Installation Guide

### Step 1: Install Python 3
If you don't have Python installed:
1. Visit the [official Python downloads page](https://www.python.org/downloads/).
2. Download the latest version for Windows.
3. **IMPORTANT**: During installation, check the box that says **"Add Python to PATH"** before clicking "Install Now".
4. Verify installation by opening Command Prompt and typing: `python --version`

### Step 2: Set Up the Application
1. Download or clone this repository to your local machine.
2. Navigate to the project folder.
3. Double-click **`install.bat`**. This will:
   - Install all necessary dependencies (`customtkinter`, `matplotlib`, `Pillow`, etc.).
   - Create a convenient **VAWC Case Logging System** shortcut on your Desktop.

## 🖱️ How to Use

1. **Launch**: Open the app using the Desktop shortcut or by running **`run.bat`**.
2. **Login**: Use your credentials (Default Admin: `admin` / `Admin@1234`).
3. **Navigation**: Use the sidebar to switch between Dashboard, Logs, Reports, and Management.
4. **Fullscreen**: Press **F8** at any time to enter or exit fullscreen mode.
5. **Add/Edit**: Changes are saved immediately to the local `vawc.db` file and reflected across the app.

## 🛡️ Data Security

- **Local Storage**: All data is stored locally in an SQLite database (`vawc_db.sqlite`), ensuring no data leaves the Barangay premises.
- **Password Security**: Uses `bcrypt` for industry-standard password hashing.
- **Backup**: Regularly use the "Backup Database" feature in the Reports tab to save your data to an external drive.

## 🛠️ Technology Stack

- **UI**: [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (Modern UI)
- **Database**: SQLite3
- **Graphics**: Matplotlib
- **Reporting**: ReportLab (PDF), OpenPyXL (Excel)
- **Security**: Bcrypt

---
*Developed for the dedicated service of Barangay Tankulan, Manolo Fortich, Bukidnon.*
