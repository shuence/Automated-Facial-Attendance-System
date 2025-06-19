import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# Constants
API_BASE_URL = "http://localhost:8000"

# User role constants
ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"
ROLE_CLASS_TEACHER = "class_teacher"

def get_token():
    return st.session_state.get('token')

def get_user():
    return st.session_state.get('user')

def login():
    st.title("DIEMS - Attendance System")
    st.subheader("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email (@dietms.org)")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/api/auth/login",
                    json={"email": email, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['token'] = data['access_token']
                    user_data = data.copy()
                    st.session_state['user'] = user_data
                    
                    st.session_state['user'] = user_data
                    st.success("Login successful!")
                    st.experimental_rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

def logout():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

def student_dashboard():
    st.title("Student Dashboard")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/students/{user['id']}/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Student Info Card
            st.write("### Personal Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**ID:** {user['student_id']}")
            with col2:
                st.info(f"**Department:** {user['department']}")
            with col3:
                st.info(f"**Year:** {user['year']} - Division {user['division']}")
            
            # Overall Attendance
            st.write("### Overall Attendance")
            col1, col2 = st.columns(2)
            with col1:
                attendance_percent = data['overall_attendance']
                color = 'red' if attendance_percent < 75 else 'green'
                st.markdown(f'<h1 style="color: {color};">{attendance_percent}%</h1>', unsafe_allow_html=True)
                st.caption("Overall Attendance")
            with col2:
                st.metric("Total Classes", data['total_classes'])
                st.metric("Classes Attended", data['classes_attended'])
            
            # Subject-wise Attendance
            st.write("### Subject-wise Attendance")
            for subject in data['subjects']:
                with st.expander(f"{subject['name']} ({subject['attendance']}%)"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Classes", subject['total_classes'])
                        st.metric("Classes Attended", subject['classes_attended'])
                    with col2:
                        st.progress(subject['attendance'] / 100)
                        if subject['attendance'] < 75:
                            st.warning("Attendance below 75%")
            
            # Recent Attendance
            st.write("### Recent Attendance")
            if data['recent_attendance']:
                df = pd.DataFrame(data['recent_attendance'])
                st.dataframe(df)
            
            # Monthly Trend
            st.write("### Monthly Attendance Trend")
            if data['monthly_trend']:
                df = pd.DataFrame(data['monthly_trend'])
                fig = px.line(df, x='month', y='attendance', 
                            title='Monthly Attendance Percentage')
                st.plotly_chart(fig)
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def class_teacher_dashboard():
    st.title("Class Teacher Dashboard")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/teachers/{user['id']}/class-dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Class Overview
            st.write("### Class Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**Department:** {user['department']}")
            with col2:
                st.info(f"**Year:** {data['class_info']['year']}")
            with col3:
                st.info(f"**Division:** {data['class_info']['division']}")
            
            # Attendance Overview
            st.write("### Class Attendance Overview")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Attendance", f"{data['class_attendance']['average']}%")
            with col2:
                st.metric("Students Below 75%", data['class_attendance']['below_threshold'])
            with col3:
                st.metric("Total Students", data['class_attendance']['total_students'])
            
            # Subject-wise Analysis
            st.write("### Subject-wise Attendance")
            if data['subject_attendance']:
                df = pd.DataFrame(data['subject_attendance'])
                fig = px.bar(df, x='subject', y='attendance', 
                           title='Average Attendance by Subject')
                st.plotly_chart(fig)
            
            # Students List
            st.write("### Students List")
            with st.expander("View Students"):
                if data['students']:
                    df = pd.DataFrame(data['students'])
                    st.dataframe(df)
                    
                    # Export option
                    if st.button("Export to CSV"):
                        df.to_csv("class_attendance.csv", index=False)
                        st.success("Data exported to class_attendance.csv")
            
            # Recent Attendance Records
            st.write("### Recent Attendance Records")
            if data['recent_records']:
                df = pd.DataFrame(data['recent_records'])
                st.dataframe(df)
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def teacher_dashboard():
    st.title("Teacher Dashboard")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/teachers/{user['id']}/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Teacher Info
            st.write("### Teacher Information")
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Department:** {user['department']}")
            with col2:
                st.info(f"**Subjects:** {', '.join(data['subjects'])}")
            
            # Today's Schedule
            st.write("### Today's Schedule")
            if data['today_schedule']:
                for session in data['today_schedule']:
                    with st.expander(f"{session['time']} - {session['subject']}"):
                        st.write(f"**Class:** {session['class']}")
                        st.write(f"**Room:** {session['room']}")
                        if session['is_practical']:
                            st.write(f"**Batch:** {session['batch']}")
                        if not session['attendance_taken']:
                            if st.button("Take Attendance", key=f"take_{session['id']}"):
                                st.session_state['current_session'] = session['id']
                                st.experimental_rerun()
            else:
                st.info("No classes scheduled for today")
            
            # Attendance Statistics
            st.write("### Attendance Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sessions", data['stats']['total_sessions'])
            with col2:
                st.metric("This Week", data['stats']['this_week_sessions'])
            with col3:
                st.metric("Average Attendance", f"{data['stats']['avg_attendance']}%")
            
            # Subject-wise Analysis
            st.write("### Subject-wise Analysis")
            if data['subject_stats']:
                df = pd.DataFrame(data['subject_stats'])
                fig = px.bar(df, x='subject', y='attendance', 
                           title='Average Attendance by Subject')
                st.plotly_chart(fig)
            
            # Recent Sessions
            st.write("### Recent Sessions")
            if data['recent_sessions']:
                df = pd.DataFrame(data['recent_sessions'])
                st.dataframe(df)
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def admin_dashboard():
    st.title("Admin Dashboard")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/admin/dashboard", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Overview Statistics
            st.write("### Overview")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Students", data['stats']['total_students'])
            with col2:
                st.metric("Total Teachers", data['stats']['total_teachers'])
            with col3:
                st.metric("Class Teachers", data['stats']['class_teachers'])
            with col4:
                st.metric("Departments", data['stats']['departments'])
            
            # Department-wise Analysis
            st.write("### Department-wise Analysis")
            if data['department_stats']:
                df = pd.DataFrame(data['department_stats'])
                fig = px.bar(df, x='department', y=['students', 'teachers'], 
                           title='Department Distribution',
                           barmode='group')
                st.plotly_chart(fig)
            
            # Attendance Overview
            st.write("### Attendance Overview")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Attendance", f"{data['attendance']['average']}%")
                st.metric("Below 75%", data['attendance']['below_threshold'])
            with col2:
                if data['attendance']['trend']:
                    df = pd.DataFrame(data['attendance']['trend'])
                    fig = px.line(df, x='date', y='attendance', 
                                title='Daily Attendance Trend')
                    st.plotly_chart(fig)
            
            # Recent Activity
            st.write("### Recent Activity")
            if data['recent_activity']:
                df = pd.DataFrame(data['recent_activity'])
                st.dataframe(df)
            
            # System Stats
            st.write("### System Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Active Sessions", data['system']['active_sessions'])
            with col2:
                st.metric("Today's Attendance", data['system']['today_attendance'])
            with col3:
                st.metric("Total Classes Today", data['system']['total_classes'])
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

def user_management():
    st.title("User Management")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Tabs for different user types
        tab1, tab2, tab3 = st.tabs(["Teachers", "Students", "Admins"])
        
        with tab1:
            st.subheader("Teachers Management")
            response = requests.get(f"{API_BASE_URL}/api/admin/users/teachers", headers=headers)
            if response.status_code == 200:
                teachers = response.json()
                if teachers:
                    df = pd.DataFrame([{
                        "ID": t["id"],
                        "Name": t["name"],
                        "Email": t["email"],
                        "Department": t.get("department", ""),
                        "Role": t["role"].replace("_", " ").title(),
                        "Subjects": ", ".join(t.get("subjects", []))
                    } for t in teachers])
                    
                    # Display teachers with action buttons
                    for idx, teacher in df.iterrows():
                        with st.expander(f"{teacher['Name']} ({teacher['Email']})"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**Department:** {teacher['Department']}")
                                st.write(f"**Role:** {teacher['Role']}")
                                st.write(f"**Subjects:** {teacher['Subjects']}")
                            with col2:
                                if st.button("Edit", key=f"edit_teacher_{teacher['ID']}"):
                                    with st.form(f"edit_teacher_form_{teacher['ID']}"):
                                        name = st.text_input("Full Name", value=teacher['Name'])
                                        email = st.text_input("Email", value=teacher['Email'])
                                        department = st.text_input("Department", value=teacher['Department'])
                                        subjects = st.text_input("Subjects (comma-separated)", value=teacher['Subjects'])
                                        role = st.selectbox("Role", ["teacher", "class_teacher"], index=0 if teacher['Role'] == "Teacher" else 1)
                                        
                                        if st.form_submit_button("Update Teacher"):
                                            try:
                                                response = requests.put(
                                                    f"{API_BASE_URL}/api/admin/users/teachers/{teacher['ID']}",
                                                    json={
                                                        "name": name,
                                                        "email": email,
                                                        "department": department,
                                                        "subjects": [s.strip() for s in subjects.split(",") if s.strip()],
                                                        "role": role
                                                    },
                                                    headers=headers
                                                )
                                                if response.status_code == 200:
                                                    st.success("Teacher updated successfully")
                                                    st.experimental_rerun()
                                                else:
                                                    st.error(f"Failed to update teacher: {response.text}")
                                            except Exception as e:
                                                st.error(f"Error: {str(e)}")
                                
                                if st.button("Delete", key=f"delete_teacher_{teacher['ID']}", type="primary"):
                                    if st.confirm(f"Are you sure you want to delete teacher {teacher['Name']}?"):
                                        try:
                                            response = requests.delete(
                                                f"{API_BASE_URL}/api/admin/users/teachers/{teacher['ID']}",
                                                headers=headers
                                            )
                                            if response.status_code == 200:
                                                st.success("Teacher deleted successfully")
                                                st.experimental_rerun()
                                            else:
                                                st.error(f"Failed to delete teacher: {response.text}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                    
                    if st.button("Add New Teacher"):
                        with st.form("new_teacher"):
                            name = st.text_input("Full Name")
                            email = st.text_input("Email (@dietms.org)")
                            password = st.text_input("Password", type="password")
                            department = st.text_input("Department", value="EXTC")
                            role = st.selectbox("Role", ["teacher", "class_teacher"], 
                                      format_func=lambda x: "Class Teacher" if x == "class_teacher" else "Teacher")
                            subjects = st.multiselect("Subjects", ["DC", "M&M", "CN", "ESD", "Mini Project"])
                            
                            if st.form_submit_button("Create Teacher"):
                                try:
                                    response = requests.post(
                                        f"{API_BASE_URL}/api/admin/users/teachers",
                                        json={
                                            "full_name": name,
                                            "email": email,
                                            "password": password,
                                            "department": department,
                                            "role": role,
                                            "subjects": subjects,
                                            "teacher_info": {
                                            "department": department,
                                            "subjects": subjects
                                            }
                                        },
                                        headers=headers
                                    )
                                    if response.status_code == 200:
                                        st.success("Teacher created successfully")
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"Failed to create teacher: {response.text}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            else:
                st.info("No teachers found")


        with tab2:
            st.subheader("Students Management")
            response = requests.get(f"{API_BASE_URL}/api/admin/users/students", headers=headers)
            if response.status_code == 200:
                students = response.json()
                if students:
                    df = pd.DataFrame([{
                        "ID": s["id"],
                        "Name": s["name"],
                        "Email": s["email"],
                        "Department": s["department"],
                        "Year": s["year"],
                        "Division": s["division"],
                        "Roll Number": s["roll_number"]
                    } for s in students])
                    
                    # Display students with action buttons
                    for idx, student in df.iterrows():
                        with st.expander(f"{student['Name']} ({student['Email']})"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**Department:** {student['Department']}")
                                st.write(f"**Year:** {student['Year']}")
                                st.write(f"**Division:** {student['Division']}")
                                st.write(f"**Roll Number:** {student['Roll Number']}")
                            with col2:
                                if st.button("Edit", key=f"edit_student_{student['ID']}"):
                                    with st.form(f"edit_student_form_{student['ID']}"):
                                        name = st.text_input("Full Name", value=student['Name'])
                                        email = st.text_input("Email", value=student['Email'])
                                        department = st.text_input("Department", value=student['Department'])
                                        year = st.selectbox("Year", ["FY", "SY", "TY", "Final"], index=["FY", "SY", "TY", "Final"].index(student['Year']))
                                        division = st.text_input("Division", value=student['Roll Number'])
                                        roll_number = st.text_input("Roll Number", value=student['Roll Number'])
                                        
                                        if st.form_submit_button("Update Student"):
                                            try:
                                                response = requests.put(
                                                    f"{API_BASE_URL}/api/admin/users/students/{student['ID']}",
                                                    json={
                                                        "name": name,
                                                        "email": email,
                                                        "department": department,
                                                        "year": year,
                                                        "division": division,
                                                        "roll_number": roll_number
                                                    },
                                                    headers=headers
                                                )
                                                if response.status_code == 200:
                                                    st.success("Student updated successfully")
                                                    st.experimental_rerun()
                                                else:
                                                    st.error(f"Failed to update student: {response.text}")
                                            except Exception as e:
                                                st.error(f"Error: {str(e)}")
                                
                                if st.button("Delete", key=f"delete_student_{student['ID']}", type="primary"):
                                    if st.confirm(f"Are you sure you want to delete student {student['Name']}?"):
                                        try:
                                            response = requests.delete(
                                                f"{API_BASE_URL}/api/admin/users/students/{student['ID']}",
                                                headers=headers
                                            )
                                            if response.status_code == 200:
                                                st.success("Student deleted successfully")
                                                st.experimental_rerun()
                                            else:
                                                st.error(f"Failed to delete student: {response.text}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                    
                    if st.button("Add New Student"):
                        with st.form("new_student"):
                            name = st.text_input("Full Name")
                            email = st.text_input("Email")
                            password = st.text_input("Password", type="password")
                            department = st.text_input("Department", value="EXTC")
                            year = st.selectbox("Year", ["FY", "SY", "TY", "Final"])
                            division = st.text_input("Division", value="B")
                            roll_number = st.text_input("Roll Number")
                            
                            if st.form_submit_button("Create Student"):
                                try:
                                    response = requests.post(
                                        f"{API_BASE_URL}/api/admin/users/students",
                                        json={
                                            "name": name,
                                            "email": email,
                                            "password": password,
                                            "department": department,
                                            "year": year,
                                            "division": division,
                                            "roll_number": roll_number
                                        },
                                        headers=headers
                                    )
                                    if response.status_code == 200:
                                        st.success("Student created successfully")
                                        st.experimental_rerun()
                                    else:
                                        st.error("Failed to create student")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                else:
                    st.info("No students found")

        with tab3:
            st.subheader("Admins Management")
            response = requests.get(f"{API_BASE_URL}/api/admin/users/admins", headers=headers)
            if response.status_code == 200:
                admins = response.json()
                if admins:
                    df = pd.DataFrame([{
                        "ID": a["id"],
                        "Name": a["name"],
                        "Email": a["email"]
                    } for a in admins])
                    
                    # Display admins with action buttons
                    for idx, admin in df.iterrows():
                        with st.expander(f"{admin['Name']} ({admin['Email']})"):
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.write(f"**Email:** {admin['Email']}")
                            with col2:
                                if st.button("Edit", key=f"edit_admin_{admin['ID']}"):
                                    with st.form(f"edit_admin_form_{admin['ID']}"):
                                        name = st.text_input("Full Name", value=admin['Name'])
                                        email = st.text_input("Email", value=admin['Email'])
                                        
                                        if st.form_submit_button("Update Admin"):
                                            try:
                                                response = requests.put(
                                                    f"{API_BASE_URL}/api/admin/users/admins/{admin['ID']}",
                                                    json={
                                                        "name": name,
                                                        "email": email
                                                    },
                                                    headers=headers
                                                )
                                                if response.status_code == 200:
                                                    st.success("Admin updated successfully")
                                                    st.experimental_rerun()
                                                else:
                                                    st.error(f"Failed to update admin: {response.text}")
                                            except Exception as e:
                                                st.error(f"Error: {str(e)}")
                                
                                if st.button("Delete", key=f"delete_admin_{admin['ID']}", type="primary"):
                                    if st.confirm(f"Are you sure you want to delete admin {admin['Name']}?"):
                                        try:
                                            response = requests.delete(
                                                f"{API_BASE_URL}/api/admin/users/admins/{admin['ID']}",
                                                headers=headers
                                            )
                                            if response.status_code == 200:
                                                st.success("Admin deleted successfully")
                                                st.experimental_rerun()
                                            else:
                                                st.error(f"Failed to delete admin: {response.text}")
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                    
                    if st.button("Add New Admin"):
                        with st.form("new_admin"):
                            name = st.text_input("Full Name")
                            email = st.text_input("Email")
                            password = st.text_input("Password", type="password")
                            
                            if st.form_submit_button("Create Admin"):
                                try:
                                    response = requests.post(
                                        f"{API_BASE_URL}/api/admin/users/admins",
                                        json={
                                            "name": name,
                                            "email": email,
                                            "password": password
                                        },
                                        headers=headers
                                    )
                                    if response.status_code == 200:
                                        st.success("Admin created successfully")
                                        st.experimental_rerun()
                                    else:
                                        st.error("Failed to create admin")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                else:
                    st.info("No admins found")

    except Exception as e:
        st.error(f"Error managing users: {str(e)}")

def student_attendance():
    st.title("Student Attendance")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/students/{user['id']}/attendance", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Monthly calendar view
            st.write("### Monthly Attendance")
            attendance_dates = {record['date']: record['status'] for record in data['attendance_records']}
            
            # Get current month dates
            today = datetime.now()
            first_day = today.replace(day=1)
            
            # Create calendar DataFrame
            calendar_dates = pd.date_range(first_day, today, freq='D')
            calendar_data = []
            
            for date in calendar_dates:
                date_str = date.strftime('%Y-%m-%d')
                status = attendance_dates.get(date_str, '-')
                calendar_data.append({
                    'Date': date.strftime('%d'),
                    'Day': date.strftime('%a'),
                    'Status': status
                })
            
            calendar_df = pd.DataFrame(calendar_data)
            st.dataframe(calendar_df, use_container_width=True)
            
            # Attendance Statistics
            st.write("### Attendance Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Classes", data['total_classes'])
            with col2:
                st.metric("Classes Attended", data['classes_attended'])
            with col3:
                attendance_percent = (data['classes_attended'] / data['total_classes'] * 100) if data['total_classes'] > 0 else 0
                st.metric("Attendance Percentage", f"{attendance_percent:.1f}%")
            
            # Subject-wise Attendance
            st.write("### Subject-wise Attendance")
            if data['subject_wise']:
                for subject in data['subject_wise']:
                    with st.expander(subject['name']):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Classes", subject['total_classes'])
                            st.metric("Classes Attended", subject['attended_classes'])
                        with col2:
                            st.metric("Percentage", f"{subject['percentage']}%")
                            if subject['percentage'] < 75:
                                st.warning("Attendance below 75%")

    except Exception as e:
        st.error(f"Error loading attendance data: {str(e)}")

def view_schedule():
    st.title("Class Schedule")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/schedule", headers=headers)
        
        if response.status_code == 200:
            schedule_data = response.json()
            
            # Weekly schedule view
            st.write("### Weekly Schedule")
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            
            for day in days:
                with st.expander(day):
                    if day in schedule_data:
                        for session in schedule_data[day]:
                            col1, col2, col3 = st.columns([2,2,1])
                            with col1:
                                st.write(f"**{session['time']}**")
                                st.write(f"Subject: {session['subject']}")
                            with col2:
                                st.write(f"Teacher: {session['teacher']}")
                                st.write(f"Room: {session['room']}")
                            with col3:
                                if session['type'] == 'practical':
                                    st.write(f"Batch: {session['batch']}")
                    else:
                        st.write("No classes scheduled")
    
    except Exception as e:
        st.error(f"Error loading schedule: {str(e)}")

def class_management():
    st.title("Class Management")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/admin/classes", headers=headers)
        
        if response.status_code == 200:
            classes = response.json()
            
            # Create new class
            if st.button("Create New Class"):
                with st.form("new_class"):
                    name = st.text_input("Class Name")
                    department = st.text_input("Department", value="EXTC")
                    year = st.selectbox("Year", ["FY", "SY", "TY", "Final"])
                    division = st.text_input("Division")
                    subjects = st.text_area("Subjects (one per line)")
                    
                    # Get teachers for class teacher assignment
                    teachers_response = requests.get(f"{API_BASE_URL}/api/admin/users/teachers", headers=headers)
                    teachers = teachers_response.json() if teachers_response.status_code == 200 else []
                    teacher_names = [f"{t['name']} ({t['email']})" for t in teachers]
                    selected_teacher = st.selectbox("Class Teacher", options=["None"] + teacher_names)
                    
                    if st.form_submit_button("Create Class"):
                        try:
                            teacher_id = None
                            if selected_teacher != "None":
                                teacher_id = next(t["id"] for t in teachers if f"{t['name']} ({t['email']})" == selected_teacher)
                            
                            response = requests.post(
                                f"{API_BASE_URL}/api/admin/classes",
                                json={
                                    "name": name,
                                    "department": department,
                                    "year": year,
                                    "division": division,
                                    "subjects": [s.strip() for s in subjects.split("\n") if s.strip()],
                                    "class_teacher_id": teacher_id
                                },
                                headers=headers
                            )
                            if response.status_code == 200:
                                st.success("Class created successfully")
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to create class: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            # Display existing classes
            st.write("### Existing Classes")
            for class_ in classes:
                with st.expander(f"{class_['name']} - {class_['department']} {class_['year']} {class_['division']}"):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.write(f"**Department:** {class_['department']}")
                        st.write(f"**Year:** {class_['year']}")
                        st.write(f"**Division:** {class_['division']}")
                    with col2:
                        st.write("**Subjects:**")
                        for subject in class_.get('subjects', []):
                            st.write(f"- {subject}")
                    with col3:
                        if st.button("Edit", key=f"edit_class_{class_['id']}"):
                            with st.form(f"edit_class_{class_['id']}"):
                                name = st.text_input("Class Name", value=class_['name'])
                                department = st.text_input("Department", value=class_['department'])
                                year = st.selectbox("Year", ["FY", "SY", "TY", "Final"], 
                                                   index=["FY", "SY", "TY", "Final"].index(class_['year']))
                                division = st.text_input("Division", value=class_['division'])
                                subjects = st.text_area("Subjects (one per line)", 
                                                      value="\n".join(class_.get('subjects', [])))
                                
                                # Teacher selection for editing
                                teachers_response = requests.get(f"{API_BASE_URL}/api/admin/users/teachers", headers=headers)
                                teachers = teachers_response.json() if teachers_response.status_code == 200 else []
                                teacher_names = [f"{t['name']} ({t['email']})" for t in teachers]
                                current_teacher = next((f"{t['name']} ({t['email']})" for t in teachers 
                                                      if t['id'] == class_.get('class_teacher_id')), "None")
                                selected_teacher = st.selectbox("Class Teacher", 
                                                             options=["None"] + teacher_names,
                                                             index=0 if current_teacher == "None" 
                                                             else teacher_names.index(current_teacher) + 1)
                                
                                if st.form_submit_button("Update Class"):
                                    try:
                                        teacher_id = None
                                        if selected_teacher != "None":
                                            teacher_id = next(t["id"] for t in teachers 
                                                           if f"{t['name']} ({t['email']})" == selected_teacher)
                                        
                                        response = requests.put(
                                            f"{API_BASE_URL}/api/admin/classes/{class_['id']}",
                                            json={
                                                "name": name,
                                                "department": department,
                                                "year": year,
                                                "division": division,
                                                "subjects": [s.strip() for s in subjects.split("\n") if s.strip()],
                                                "class_teacher_id": teacher_id
                                            },
                                            headers=headers
                                        )
                                        if response.status_code == 200:
                                            st.success("Class updated successfully")
                                            st.experimental_rerun()
                                        else:
                                            st.error(f"Failed to update class: {response.text}")
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        
                        if st.button("Delete", key=f"delete_class_{class_['id']}", type="primary"):
                            if st.confirm(f"Are you sure you want to delete class {class_['name']}?"):
                                try:
                                    response = requests.delete(
                                        f"{API_BASE_URL}/api/admin/classes/{class_['id']}",
                                        headers=headers
                                    )
                                    if response.status_code == 200:
                                        st.success("Class deleted successfully")
                                        st.experimental_rerun()
                                    else:
                                        st.error(f"Failed to delete class: {response.text}")
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
        else:
            st.error("Failed to fetch classes")
    except Exception as e:
        st.error(f"Error managing classes: {str(e)}")

def manage_schedule():
    st.title("Schedule Management")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get all schedules
        response = requests.get(f"{API_BASE_URL}/api/admin/schedules", headers=headers)
        if response.status_code == 200:
            schedules = response.json()
            
            # Create new schedule
            if st.button("Create New Schedule"):
                with st.form("new_schedule"):
                    # Class selection
                    classes_response = requests.get(f"{API_BASE_URL}/api/admin/classes", headers=headers)
                    classes = classes_response.json() if classes_response.status_code == 200 else []
                    class_names = [f"{c['name']} - {c['department']} {c['year']} {c['division']}" for c in classes]
                    selected_class = st.selectbox("Select Class", options=class_names)
                    class_id = next(c["id"] for c in classes if f"{c['name']} - {c['department']} {c['year']} {c['division']}" == selected_class)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
                        start_time = st.time_input("Start Time")
                        duration = st.selectbox("Duration (hours)", [1, 2])
                    with col2:
                        session_type = st.selectbox("Session Type", ["lecture", "practical", "seminar", "mini_project", "off", "other"])
                        room = st.text_input("Room Number")
                        batch = st.text_input("Batch (for practicals)", "")
                    
                    if st.form_submit_button("Create Schedule"):
                        try:
                            end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=duration)).time()
                            response = requests.post(
                                f"{API_BASE_URL}/api/admin/schedules",
                                json={
                                    "class_id": class_id,
                                    "day": day,
                                    "start_time": start_time.strftime("%H:%M"),
                                    "end_time": end_time.strftime("%H:%M"),
                                    "duration": duration,
                                    "type": session_type,
                                    "room": room,
                                    "batch": batch if batch else None
                                },
                                headers=headers
                            )
                            if response.status_code == 200:
                                st.success("Schedule created successfully")
                                st.experimental_rerun()
                            else:
                                st.error(f"Failed to create schedule: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            # Display existing schedules
            st.write("### Existing Schedules")
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
            for day in days:
                with st.expander(day):
                    day_schedules = [s for s in schedules if s["day"].lower() == day.lower()]
                    if day_schedules:
                        for schedule in sorted(day_schedules, key=lambda x: x["start_time"]):
                            with st.container():
                                col1, col2, col3 = st.columns([3, 2, 1])
                                with col1:
                                    st.write(f"**Time:** {schedule['start_time']} - {schedule['end_time']}")
                                    st.write(f"**Class:** {schedule.get('class_name', 'Unknown')}")
                                    st.write(f"**Room:** {schedule.get('room', 'TBD')}")
                                with col2:
                                    st.write(f"**Type:** {schedule['type'].title()}")
                                    if schedule.get('batch'):
                                        st.write(f"**Batch:** {schedule['batch']}")
                                with col3:
                                    if st.button("Edit", key=f"edit_{schedule['id']}"):
                                        with st.form(f"edit_schedule_{schedule['id']}"):
                                            start_time = st.time_input("Start Time", datetime.strptime(schedule['start_time'], "%H:%M").time())
                                            duration = st.selectbox("Duration (hours)", [1, 2], index=0 if schedule.get('duration', 1) == 1 else 1)
                                            session_type = st.selectbox("Session Type", 
                                                ["lecture", "practical", "seminar", "mini_project", "off", "other"],
                                                index=["lecture", "practical", "seminar", "mini_project", "off", "other"].index(schedule['type']))
                                            room = st.text_input("Room Number", value=schedule.get('room', ''))
                                            batch = st.text_input("Batch", value=schedule.get('batch', ''))
                                            
                                            if st.form_submit_button("Update"):
                                                try:
                                                    end_time = (datetime.combine(datetime.today(), start_time) + timedelta(hours=duration)).time()
                                                    response = requests.put(
                                                        f"{API_BASE_URL}/api/admin/schedules/{schedule['id']}",
                                                        json={
                                                            "start_time": start_time.strftime("%H:%M"),
                                                            "end_time": end_time.strftime("%H:%M"),
                                                            "duration": duration,
                                                            "type": session_type,
                                                            "room": room,
                                                            "batch": batch if batch else None
                                                        },
                                                        headers=headers
                                                    )
                                                    if response.status_code == 200:
                                                        st.success("Schedule updated successfully")
                                                        st.experimental_rerun()
                                                    else:
                                                        st.error(f"Failed to update schedule: {response.text}")
                                                except Exception as e:
                                                    st.error(f"Error: {str(e)}")
                                    
                                    if st.button("Delete", key=f"delete_{schedule['id']}", type="primary"):
                                        if st.confirm(f"Are you sure you want to delete this schedule?"):
                                            try:
                                                response = requests.delete(
                                                    f"{API_BASE_URL}/api/admin/schedules/{schedule['id']}",
                                                    headers=headers
                                                )
                                                if response.status_code == 200:
                                                    st.success("Schedule deleted successfully")
                                                    st.experimental_rerun()
                                                else:
                                                    st.error(f"Failed to delete schedule: {response.text}")
                                            except Exception as e:
                                                st.error(f"Error: {str(e)}")
                    else:
                        st.info("No schedules for this day")
    except Exception as e:
        st.error(f"Error managing schedules: {str(e)}")

def take_attendance():
    st.title("Take Attendance")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get user's classes
        response = requests.get(f"{API_BASE_URL}/api/teachers/{user['id']}/classes", headers=headers)
        
        if response.status_code == 200:
            classes = response.json()
            
            # Class selection
            selected_class = st.selectbox(
                "Select Class",
                options=[f"{c['name']} - {c['subject']}" for c in classes],
                format_func=lambda x: x
            )
            
            if selected_class:
                class_id = next(c['id'] for c in classes if f"{c['name']} - {c['subject']}" == selected_class)
                
                # Get class students
                students_response = requests.get(
                    f"{API_BASE_URL}/api/classes/{class_id}/students",
                    headers=headers
                )
                
                if students_response.status_code == 200:
                    students = students_response.json()
                    
                    # Attendance form
                    st.write("### Mark Attendance")
                    date = st.date_input("Date", datetime.now())
                    
                    with st.form("attendance_form"):
                        attendance_data = {}
                        
                        for student in students:
                            attendance_data[student['id']] = st.checkbox(
                                f"{student['name']} ({student['roll_number']})",
                                key=f"attend_{student['id']}"
                            )
                        
                        note = st.text_area("Notes (optional)")
                        
                        if st.form_submit_button("Submit Attendance"):
                            submit_response = requests.post(
                                f"{API_BASE_URL}/api/attendance",
                                json={
                                    "class_id": class_id,
                                    "date": date.strftime("%Y-%m-%d"),
                                    "attendance": attendance_data,
                                    "note": note
                                },
                                headers=headers
                            )
                            
                            if submit_response.status_code == 200:
                                st.success("Attendance submitted successfully")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to submit attendance")
    
    except Exception as e:
        st.error(f"Error taking attendance: {str(e)}")

def view_reports():
    st.title("View Reports")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get user's classes
        response = requests.get(f"{API_BASE_URL}/api/teachers/{user['id']}/classes", headers=headers)
        
        if response.status_code == 200:
            classes = response.json()
            
            # Class selection
            selected_class = st.selectbox(
                "Select Class",
                options=[f"{c['name']} - {c['subject']}" for c in classes],
                format_func=lambda x: x
            )
            
            if selected_class:
                class_id = next(c['id'] for c in classes if f"{c['name']} - {c['subject']}" == selected_class)
                
                # Date range selection
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
                with col2:
                    end_date = st.date_input("To Date", datetime.now())
                
                # Get attendance reports
                report_response = requests.get(
                    f"{API_BASE_URL}/api/reports/{class_id}",
                    params={
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d")
                    },
                    headers=headers
                )
                
                if report_response.status_code == 200:
                    report_data = report_response.json()
                    
                    # Display overall statistics
                    st.write("### Overall Statistics")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Attendance", f"{report_data['average_attendance']}%")
                    with col2:
                        st.metric("Total Classes", report_data['total_classes'])
                    with col3:
                        st.metric("Below 75%", report_data['students_below_threshold'])
                    
                    # Student-wise attendance
                    st.write("### Student-wise Attendance")
                    if 'student_attendance' in report_data:
                        df = pd.DataFrame(report_data['student_attendance'])
                        st.dataframe(df)
                        
                        # Download options
                        if st.button("Download Report"):
                            df.to_csv("attendance_report.csv", index=False)
                            st.success("Report downloaded as attendance_report.csv")
                    
                    # Graphical representation
                    st.write("### Attendance Trends")
                    if 'daily_attendance' in report_data:
                        daily_df = pd.DataFrame(report_data['daily_attendance'])
                        fig = px.line(daily_df, x='date', y='attendance_percentage',
                                    title='Daily Attendance Trend')
                        st.plotly_chart(fig)
    
    except Exception as e:
        st.error(f"Error viewing reports: {str(e)}")

def system_reports():
    st.title("System Reports")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Report type selection
        report_type = st.selectbox(
            "Select Report Type",
            ["Department-wise", "Year-wise", "Subject-wise", "Teacher-wise"]
        )
        
        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("To Date", datetime.now())
        
        if st.button("Generate Report"):
            response = requests.get(
                f"{API_BASE_URL}/api/reports/system",
                params={
                    "type": report_type.lower(),
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                headers=headers
            )
            
            if response.status_code == 200:
                report_data = response.json()
                
                # Display report based on type
                if report_type == "Department-wise":
                    st.write("### Department-wise Attendance Report")
                    df = pd.DataFrame(report_data['data'])
                    
                    # Bar chart
                    fig = px.bar(df, x='department', y='attendance_percentage',
                                title='Attendance Percentage by Department')
                    st.plotly_chart(fig)
                    
                    # Detailed table
                    st.dataframe(df)
                
                elif report_type == "Year-wise":
                    st.write("### Year-wise Attendance Report")
                    df = pd.DataFrame(report_data['data'])
                    
                    # Bar chart
                    fig = px.bar(df, x='year', y='attendance_percentage',
                                title='Attendance Percentage by Year')
                    st.plotly_chart(fig)
                    
                    # Detailed table
                    st.dataframe(df)
                
                elif report_type == "Subject-wise":
                    st.write("### Subject-wise Attendance Report")
                    df = pd.DataFrame(report_data['data'])
                    
                    # Bar chart
                    fig = px.bar(df, x='subject', y='attendance_percentage',
                                title='Attendance Percentage by Subject')
                    st.plotly_chart(fig)
                    
                    # Detailed table
                    st.dataframe(df)
                
                elif report_type == "Teacher-wise":
                    st.write("### Teacher-wise Attendance Report")
                    df = pd.DataFrame(report_data['data'])
                    
                    # Bar chart
                    fig = px.bar(df, x='teacher', y='attendance_percentage',
                                title='Attendance Percentage by Teacher')
                    st.plotly_chart(fig)
                    
                    # Detailed table
                    st.dataframe(df)
                
                # Download option
                if st.button("Download Report"):
                    df.to_csv("system_report.csv", index=False)
                    st.success("Report downloaded as system_report.csv")
    
    except Exception as e:
        st.error(f"Error generating system reports: {str(e)}")

def system_settings():
    st.title("System Settings")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get current settings
        response = requests.get(f"{API_BASE_URL}/api/admin/settings", headers=headers)
        
        if response.status_code == 200:
            settings = response.json()
            
            # General Settings
            st.write("### General Settings")
            with st.form("general_settings"):
                col1, col2 = st.columns(2)
                with col1:
                    min_attendance = st.number_input(
                        "Minimum Attendance Requirement (%)",
                        value=settings.get('min_attendance', 75),
                        min_value=0,
                        max_value=100
                    )
                    session_timeout = st.number_input(
                        "Session Timeout (minutes)",
                        value=settings.get('session_timeout', 30),
                        min_value=5
                    )
                
                with col2:
                    auto_logout = st.checkbox(
                        "Enable Auto Logout",
                        value=settings.get('auto_logout', True)
                    )
                    maintenance_mode = st.checkbox(
                        "Maintenance Mode",
                        value=settings.get('maintenance_mode', False)
                    )
                
                if st.form_submit_button("Save General Settings"):
                    update_response = requests.put(
                        f"{API_BASE_URL}/api/admin/settings/general",
                        json={
                            "min_attendance": min_attendance,
                            "session_timeout": session_timeout,
                            "auto_logout": auto_logout,
                            "maintenance_mode": maintenance_mode
                        },
                        headers=headers
                    )
                    if update_response.status_code == 200:
                        st.success("Settings updated successfully")
                    else:
                        st.error("Failed to update settings")
            
            # Notification Settings
            st.write("### Notification Settings")
            with st.form("notification_settings"):
                email_notifications = st.checkbox(
                    "Enable Email Notifications",
                    value=settings.get('email_notifications', True)
                )
                notify_low_attendance = st.checkbox(
                    "Notify on Low Attendance",
                    value=settings.get('notify_low_attendance', True)
                )
                notify_missed_classes = st.checkbox(
                    "Notify on Missed Classes",
                    value=settings.get('notify_missed_classes', True)
                )
                
                if st.form_submit_button("Save Notification Settings"):
                    update_response = requests.put(
                        f"{API_BASE_URL}/api/admin/settings/notifications",
                        json={
                            "email_notifications": email_notifications,
                            "notify_low_attendance": notify_low_attendance,
                            "notify_missed_classes": notify_missed_classes
                        },
                        headers=headers
                    )
                    if update_response.status_code == 200:
                        st.success("Notification settings updated successfully")
                    else:
                        st.error("Failed to update notification settings")
            
            # Backup Settings
            st.write("### Backup Settings")
            with st.form("backup_settings"):
                auto_backup = st.checkbox(
                    "Enable Automatic Backups",
                    value=settings.get('auto_backup', True)
                )
                backup_frequency = st.selectbox(
                    "Backup Frequency",
                    ["Daily", "Weekly", "Monthly"],
                    index=["Daily", "Weekly", "Monthly"].index(
                        settings.get('backup_frequency', "Weekly")
                    )
                )
                retention_days = st.number_input(
                    "Backup Retention (days)",
                    value=settings.get('retention_days', 30),
                    min_value=1
                )
                
                if st.form_submit_button("Save Backup Settings"):
                    update_response = requests.put(
                        f"{API_BASE_URL}/api/admin/settings/backup",
                        json={
                            "auto_backup": auto_backup,
                            "backup_frequency": backup_frequency,
                            "retention_days": retention_days
                        },
                        headers=headers
                    )
                    if update_response.status_code == 200:
                        st.success("Backup settings updated successfully")
                    else:
                        st.error("Failed to update backup settings")
            
            # System Maintenance
            st.write("### System Maintenance")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Backup Now"):
                    backup_response = requests.post(
                        f"{API_BASE_URL}/api/admin/maintenance/backup",
                        headers=headers
                    )
                    if backup_response.status_code == 200:
                        st.success("Backup created successfully")
                    else:
                        st.error("Failed to create backup")
            
            with col2:
                if st.button("Clear Cache"):
                    cache_response = requests.post(
                        f"{API_BASE_URL}/api/admin/maintenance/clear-cache",
                        headers=headers
                    )
                    if cache_response.status_code == 200:
                        st.success("Cache cleared successfully")
                    else:
                        st.error("Failed to clear cache")
    
    except Exception as e:
        st.error(f"Error managing system settings: {str(e)}")

def user_profile():
    st.title("User Profile")
    user = get_user()
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/users/{user['id']}/profile", headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            
            # Display profile information
            st.write("### Basic Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Name:** {profile['full_name']}")
                st.write(f"**Email:** {profile['email']}")
                st.write(f"**Role:** {profile['role'].replace('_', ' ').title()}")
            
            with col2:
                if 'department' in profile:
                    st.write(f"**Department:** {profile['department']}")
                if 'subjects' in profile:
                    st.write("**Subjects:**")
                    for subject in profile['subjects']:
                        st.write(f"- {subject}")
            
            # Student-specific information
            if user['role'] == ROLE_STUDENT:
                st.write("### Academic Information")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Student ID:** {profile['student_info']['student_id']}")
                with col2:
                    st.write(f"**Year:** {profile['student_info']['year']}")
                with col3:
                    st.write(f"**Division:** {profile['student_info']['division']}")
            
            # Change password form
            st.write("### Change Password")
            with st.form("change_password"):
                current_password = st.text_input("Current Password", type="password")
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Change Password"):
                    if new_password != confirm_password:
                        st.error("New passwords do not match")
                    else:
                        response = requests.post(
                            f"{API_BASE_URL}/api/users/{user['id']}/change-password",
                            json={
                                "current_password": current_password,
                                "new_password": new_password
                            },
                            headers=headers
                        )
                        if response.status_code == 200:
                            st.success("Password changed successfully")
                            st.session_state['show_logout_message'] = True
                            logout()
                        else:
                            st.error("Failed to change password")
            
            # Update profile form
            st.write("### Update Profile")
            with st.form("update_profile"):
                full_name = st.text_input("Full Name", value=profile['full_name'])
                email = st.text_input("Email", value=profile['email'])
                
                if st.form_submit_button("Update Profile"):
                    response = requests.put(
                        f"{API_BASE_URL}/api/users/{user['id']}/profile",
                        json={
                            "full_name": full_name,
                            "email": email
                        },
                        headers=headers
                    )
                    if response.status_code == 200:
                        st.success("Profile updated successfully")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to update profile")
    
    except Exception as e:
        st.error(f"Error loading profile: {str(e)}")

def main():
    st.set_page_config(
        page_title="DIET MS - Attendance System",
        page_icon="✓",
        layout="wide"
    )

    if 'token' not in st.session_state:
        login()
        return    # User is logged in
    user = get_user()
    if not user:
        login()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.write(f"Welcome, {user.get('full_name', 'User')}")
        st.write(f"Role: {user.get('role', 'Unknown').replace('_', ' ').title()}")
        
        if user['role'] == ROLE_STUDENT:
            page = st.radio("Navigation", [
                "Dashboard",
                "My Attendance",
                "View Schedule",
                "Profile"
            ])
        elif user['role'] == ROLE_CLASS_TEACHER:
            page = st.radio("Navigation", [
                "Dashboard",
                "Class Management",
                "Take Attendance",
                "View Reports",
                "Schedule",
                "Profile"
            ])
        elif user['role'] == ROLE_TEACHER:
            page = st.radio("Navigation", [
                "Dashboard",
                "Take Attendance",
                "View Reports",
                "Schedule",
                "Profile"
            ])
        elif user['role'] == ROLE_ADMIN:
            page = st.radio("Navigation", [
                "Dashboard",
                "User Management",
                "Class Management",
                "Schedule Management",
                "Reports",
                "System Settings"
            ])
        
        if st.button("Logout"):
            logout()
            return
    
    # Display selected page
    if user['role'] == ROLE_STUDENT:
        if page == "Dashboard":
            student_dashboard()
        elif page == "My Attendance":
            student_attendance()
        elif page == "View Schedule":
            view_schedule()
        elif page == "Profile":
            user_profile()
    
    elif user['role'] == ROLE_CLASS_TEACHER:
        if page == "Dashboard":
            class_teacher_dashboard()        elif page == "Class Management":
            class_management()
        elif page == "Take Attendance":
            take_attendance()
        elif page == "View Reports":
            view_reports()
        elif page == "Schedule":
            manage_schedule()
        elif page == "Profile":
            user_profile()
    
    elif user['role'] == ROLE_TEACHER:
        if page == "Dashboard":
            teacher_dashboard()
        elif page == "Take Attendance":
            take_attendance()
        elif page == "View Reports":
            view_reports()
        elif page == "Schedule":
            view_schedule()
        elif page == "Profile":
            user_profile()
    
    elif user['role'] == ROLE_ADMIN:
        if page == "Dashboard":
            admin_dashboard()
        elif page == "User Management":
            user_management()
        elif page == "Class Management":
            class_management()
        elif page == "Schedule Management":
            schedule_management()
        elif page == "Reports":
            system_reports()
        elif page == "System Settings":
            system_settings()

if __name__ == "__main__":
    main()
