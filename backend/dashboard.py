import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import json
import time

# Constants
API_BASE_URL = "http://localhost:8000"

def get_token():
    return st.session_state.get('token')

def get_user():
    return st.session_state.get('user')

def login():
    st.title("Login")
    
    with st.form("login_form"):
        email = st.text_input("Email")
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
                    st.session_state['user'] = {
                        'id': data['user_id'],
                        'email': data['email'],
                        'full_name': data['full_name'],
                        'role': data['role']
                    }
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

def student_dashboard(student_id):
    st.title("Student Dashboard")
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/dashboard/student/{student_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Student Info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Department", data['department'])
            with col2:
                st.metric("Year", data['year'])
            with col3:
                st.metric("Division", data['division'])
            
            # Monthly Attendance Summary
            st.subheader("This Month's Attendance")
            monthly_data = data['attendance_summary']['this_month']
            attendance_percentage = monthly_data['attendance_percentage']
            
            progress_color = 'red' if attendance_percentage < 75 else 'green'
            st.progress(attendance_percentage / 100, text=f"{attendance_percentage:.1f}%")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Classes", monthly_data['total_classes'])
            with col2:
                st.metric("Classes Attended", monthly_data['attended_classes'])
            
            # Subject-wise Attendance
            st.subheader("Subject-wise Attendance")
            subject_data = data['attendance_summary']['by_subject']
            
            if subject_data:
                df = pd.DataFrame([
                    {
                        'Subject': subject,
                        'Attendance': stats['percentage'],
                        'Present': stats['present'],
                        'Total': stats['total']
                    }
                    for subject, stats in subject_data.items()
                ])
                
                fig = px.bar(df, x='Subject', y='Attendance',
                            title='Subject-wise Attendance Percentage',
                            labels={'Attendance': 'Attendance %'})
                st.plotly_chart(fig)
            
            # Recent Attendance
            st.subheader("Recent Attendance")
            if data['recent_attendance']:
                recent_df = pd.DataFrame(data['recent_attendance'])
                recent_df['date'] = pd.to_datetime(recent_df['date']).dt.strftime('%Y-%m-%d')
                st.dataframe(recent_df)
            
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")

def teacher_dashboard(teacher_id):
    st.title("Teacher Dashboard")
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/dashboard/teacher/{teacher_id}", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Teacher Info
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Department", data['department'])
            with col2:
                st.metric("Role", data['role'].replace('_', ' ').title())
            
            # Summary Metrics
            st.subheader("Session Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sessions", data['summary']['total_sessions'])
            with col2:
                st.metric("This Month", data['summary']['this_month_sessions'])
            with col3:
                st.metric("Last 30 Days", data['summary']['last_30_days_sessions'])
            
            # Subject Statistics
            st.subheader("Subject Statistics")
            if data['subject_stats']:
                subject_df = pd.DataFrame([
                    {
                        'Subject': subject,
                        'Total Sessions': stats['total_sessions'],
                        'Average Attendance': stats['average_attendance']
                    }
                    for subject, stats in data['subject_stats'].items()
                ])
                
                fig = px.bar(subject_df, x='Subject', y='Average Attendance',
                            title='Average Attendance by Subject',
                            labels={'Average Attendance': 'Average Attendance %'})
                st.plotly_chart(fig)
            
            # Class Statistics
            st.subheader("Class Statistics")
            if data['class_stats']:
                class_df = pd.DataFrame(data['class_stats'])
                fig = px.bar(class_df, x='class_name', y='average_attendance',
                            title='Average Attendance by Class',
                            labels={'class_name': 'Class', 'average_attendance': 'Average Attendance %'})
                st.plotly_chart(fig)
            
            # Recent Sessions
            st.subheader("Recent Sessions")
            if data['recent_sessions']:
                recent_df = pd.DataFrame(data['recent_sessions'])
                recent_df['date'] = pd.to_datetime(recent_df['date']).dt.strftime('%Y-%m-%d')
                st.dataframe(recent_df)
            
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")

def admin_dashboard():
    st.title("Admin Dashboard")
    
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/dashboard/stats", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # User Statistics
            st.subheader("User Statistics")
            user_counts = data['user_counts']
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Users", user_counts['total'])
            with col2:
                st.metric("Students", user_counts['student'])
            with col3:
                st.metric("Teachers", user_counts['teacher'])
            with col4:
                st.metric("Class Teachers", user_counts['class_teacher'])
            with col5:
                st.metric("Admins", user_counts['admin'])
            
            # Attendance Summary
            st.subheader("Attendance Summary")
            attendance = data['attendance_summary']
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Sessions", attendance['total_sessions'])
            with col2:
                st.metric("This Month", attendance['this_month_sessions'])
            
            # Monthly Trend
            if attendance['monthly_trend']:
                monthly_df = pd.DataFrame([
                    {'Month': datetime.strptime(str(month), "%m").strftime("%B"),
                     'Sessions': sessions}
                    for month, sessions in attendance['monthly_trend'].items()
                ])
                
                fig = px.line(monthly_df, x='Month', y='Sessions',
                             title='Monthly Attendance Sessions',
                             labels={'Sessions': 'Number of Sessions'})
                st.plotly_chart(fig)
            
            # Department Statistics
            st.subheader("Department Statistics")
            if attendance['department_stats']:
                dept_df = pd.DataFrame([
                    {
                        'Department': dept,
                        'Average Attendance': stats['average_attendance'],
                        'Total Sessions': stats['total_sessions']
                    }
                    for dept, stats in attendance['department_stats'].items()
                ])
                
                fig = px.bar(dept_df, x='Department', y='Average Attendance',
                            title='Average Attendance by Department',
                            labels={'Average Attendance': 'Average Attendance %'})
                st.plotly_chart(fig)
            
    except Exception as e:
        st.error(f"Error fetching dashboard data: {str(e)}")

def student_attendance(student_id):
    st.title("My Attendance")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/students/{student_id}/attendance", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # Calendar view
            st.subheader("Attendance Calendar")
            dates = pd.date_range(start=datetime.now().replace(day=1), end=datetime.now(), freq='D')
            calendar_data = {date.strftime('%Y-%m-%d'): False for date in dates}
            
            for record in data['attendance_records']:
                calendar_data[record['date']] = record['present']
            
            # Convert to DataFrame for visualization
            df = pd.DataFrame(list(calendar_data.items()), columns=['Date', 'Present'])
            df['Date'] = pd.to_datetime(df['Date'])
            
            fig = px.scatter(df, x='Date', y=['Present'],
                           title='Attendance Calendar',
                           color='Present',
                           color_discrete_map={True: 'green', False: 'red'})
            st.plotly_chart(fig)
            
            # Detailed Records
            st.subheader("Detailed Records")
            if data['attendance_records']:
                records_df = pd.DataFrame(data['attendance_records'])
                records_df['date'] = pd.to_datetime(records_df['date']).dt.strftime('%Y-%m-%d')
                st.dataframe(records_df)
            
    except Exception as e:
        st.error(f"Error fetching attendance data: {str(e)}")

def mark_attendance(student_id):
    st.title("Mark Attendance")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get today's schedule
        response = requests.get(f"{API_BASE_URL}/api/students/{student_id}/schedule/today", headers=headers)
        
        if response.status_code == 200:
            schedule = response.json()
            
            if not schedule['classes']:
                st.info("No classes scheduled for today.")
                return
            
            st.subheader("Today's Classes")
            for class_info in schedule['classes']:
                with st.expander(f"{class_info['subject']} - {class_info['time']}"):
                    if not class_info['attendance_marked']:
                        if st.button("Mark Attendance", key=class_info['id']):
                            # Implement facial recognition attendance marking here
                            mark_response = requests.post(
                                f"{API_BASE_URL}/api/attendance/mark",
                                headers=headers,
                                json={
                                    "student_id": student_id,
                                    "class_id": class_info['id']
                                }
                            )
                            if mark_response.status_code == 200:
                                st.success("Attendance marked successfully!")
                            else:
                                st.error("Failed to mark attendance.")
                    else:
                        st.success("Attendance already marked")
                    
    except Exception as e:
        st.error(f"Error marking attendance: {str(e)}")

def view_schedule(student_id):
    st.title("Class Schedule")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/students/{student_id}/schedule", headers=headers)
        
        if response.status_code == 200:
            schedule = response.json()
            
            # Weekly Schedule
            st.subheader("Weekly Schedule")
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            for day in days:
                with st.expander(day):
                    if day in schedule:
                        for class_info in schedule[day]:
                            st.write(f"⏰ {class_info['time']}: {class_info['subject']} ({class_info['teacher']})")
                    else:
                        st.write("No classes scheduled")
            
    except Exception as e:
        st.error(f"Error fetching schedule: {str(e)}")

def take_attendance(teacher_id):
    st.title("Take Attendance")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get teacher's classes
        response = requests.get(f"{API_BASE_URL}/api/teachers/{teacher_id}/classes", headers=headers)
        
        if response.status_code == 200:
            classes = response.json()
            
            # Class selection
            selected_class = st.selectbox("Select Class", 
                [f"{c['subject']} - {c['class_name']}" for c in classes],
                format_func=lambda x: x)
            
            if selected_class:
                class_id = next(c['id'] for c in classes if f"{c['subject']} - {c['class_name']}" == selected_class)
                
                # Get students in class
                students_response = requests.get(f"{API_BASE_URL}/api/teachers/class/{class_id}/students", headers=headers)
                if students_response.status_code == 200:
                    students = students_response.json()
                    
                    st.subheader("Mark Attendance")
                    date = st.date_input("Date", datetime.now())
                    
                    # Create attendance form
                    with st.form("attendance_form"):
                        attendance_data = {}
                        for student in students:
                            attendance_data[student['id']] = st.checkbox(
                                f"{student['name']} ({student['roll_number']})",
                                key=f"attend_{student['id']}"
                            )
                        
                        if st.form_submit_button("Submit Attendance"):
                            submit_response = requests.post(
                                f"{API_BASE_URL}/api/attendance/bulk",
                                headers=headers,
                                json={
                                    "class_id": class_id,
                                    "date": date.strftime("%Y-%m-%d"),
                                    "attendance": attendance_data
                                }
                            )
                            if submit_response.status_code == 200:
                                st.success("Attendance submitted successfully!")
                            else:
                                st.error("Failed to submit attendance.")
                    
    except Exception as e:
        st.error(f"Error taking attendance: {str(e)}")

def view_reports(teacher_id):
    st.title("Attendance Reports")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get teacher's classes
        response = requests.get(f"{API_BASE_URL}/api/teachers/{teacher_id}/classes", headers=headers)
        
        if response.status_code == 200:
            classes = response.json()
            
            # Class selection
            selected_class = st.selectbox("Select Class", 
                [f"{c['subject']} - {c['class_name']}" for c in classes],
                format_func=lambda x: x)
            
            if selected_class:
                class_id = next(c['id'] for c in classes if f"{c['subject']} - {c['class_name']}" == selected_class)
                
                # Date range selection
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                with col2:
                    end_date = st.date_input("End Date", datetime.now())
                
                # Get attendance reports
                reports_response = requests.get(
                    f"{API_BASE_URL}/api/reports/class/{class_id}",
                    params={"start_date": start_date.strftime("%Y-%m-%d"),
                           "end_date": end_date.strftime("%Y-%m-%d")},
                    headers=headers
                )
                
                if reports_response.status_code == 200:
                    reports = reports_response.json()
                    
                    # Overall statistics
                    st.subheader("Class Statistics")
                    stats = reports['statistics']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Average Attendance", f"{stats['average_attendance']:.1f}%")
                    with col2:
                        st.metric("Total Classes", stats['total_classes'])
                    with col3:
                        st.metric("Students Below 75%", stats['students_below_threshold'])
                    
                    # Student-wise attendance
                    st.subheader("Student-wise Attendance")
                    student_df = pd.DataFrame(reports['student_attendance'])
                    fig = px.bar(student_df, x='student_name', y='attendance_percentage',
                                title='Student-wise Attendance Percentage')
                    st.plotly_chart(fig)
                    
                    # Detailed records
                    st.subheader("Detailed Records")
                    st.dataframe(student_df)
                    
    except Exception as e:
        st.error(f"Error viewing reports: {str(e)}")

def manage_classes(teacher_id):
    st.title("Manage Classes")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get teacher's classes
        response = requests.get(f"{API_BASE_URL}/api/teachers/{teacher_id}/classes", headers=headers)
        
        if response.status_code == 200:
            classes = response.json()
            
            st.subheader("Your Classes")
            for class_info in classes:
                with st.expander(f"{class_info['subject']} - {class_info['class_name']}"):
                    st.write(f"📚 Subject: {class_info['subject']}")
                    st.write(f"👥 Class: {class_info['class_name']}")
                    st.write(f"📅 Schedule: {class_info['schedule']}")
                    
                    if st.button("View Students", key=f"view_{class_info['id']}"):
                        students_response = requests.get(
                            f"{API_BASE_URL}/api/teachers/class/{class_info['id']}/students",
                            headers=headers
                        )
                        if students_response.status_code == 200:
                            students = students_response.json()
                            st.write("### Students")
                            for student in students:
                                st.write(f"- {student['name']} ({student['roll_number']})")
                    
    except Exception as e:
        st.error(f"Error managing classes: {str(e)}")

def manage_schedule(teacher_id):
    st.title("Class Schedule")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get teacher's schedule
        response = requests.get(f"{API_BASE_URL}/api/teachers/{teacher_id}/schedule", headers=headers)
        
        if response.status_code == 200:
            schedule = response.json()
            
            st.subheader("Weekly Schedule")
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            
            for day in days:
                with st.expander(day):
                    if day in schedule:
                        for class_info in schedule[day]:
                            st.write(f"⏰ {class_info['time']}")
                            st.write(f"📚 {class_info['subject']} ({class_info['class_name']})")
                            st.write(f"📍 {class_info['room']}")
                    else:
                        st.write("No classes scheduled")
            
    except Exception as e:
        st.error(f"Error viewing schedule: {str(e)}")

def user_profile(user_id):
    st.title("User Profile")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/users/{user_id}/profile", headers=headers)
        
        if response.status_code == 200:
            profile = response.json()
            
            # Display profile information
            st.subheader("Personal Information")
            col1, col2 = st.columns(2)
            with col1:
                st.write("### Basic Details")
                st.write(f"**Name:** {profile['full_name']}")
                st.write(f"**Email:** {profile['email']}")
                st.write(f"**Role:** {profile['role'].replace('_', ' ').title()}")
                if 'department' in profile:
                    st.write(f"**Department:** {profile['department']}")
            
            with col2:
                st.write("### Additional Information")
                if 'roll_number' in profile:
                    st.write(f"**Roll Number:** {profile['roll_number']}")
                if 'year' in profile:
                    st.write(f"**Year:** {profile['year']}")
                if 'division' in profile:
                    st.write(f"**Division:** {profile['division']}")
            
            # Profile Settings
            st.subheader("Profile Settings")
            with st.form("profile_settings"):
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Change Password"):
                    if new_password != confirm_password:
                        st.error("Passwords do not match!")
                    else:
                        update_response = requests.post(
                            f"{API_BASE_URL}/api/users/{user_id}/change-password",
                            headers=headers,
                            json={"new_password": new_password}
                        )
                        if update_response.status_code == 200:
                            st.success("Password updated successfully!")
                        else:
                            st.error("Failed to update password.")
            
    except Exception as e:
        st.error(f"Error loading profile: {str(e)}")

def user_management():
    st.title("User Management")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Tabs for different user types
        tab1, tab2, tab3 = st.tabs(["Teachers", "Students", "Admins"])
        
        with tab1:
            response = requests.get(f"{API_BASE_URL}/api/admin/users/teachers", headers=headers)
            if response.status_code == 200:
                teachers = response.json()
                st.subheader("Teachers Management")
                
                # Add new teacher
                with st.expander("Add New Teacher"):
                    with st.form("add_teacher"):
                        name = st.text_input("Full Name")
                        email = st.text_input("Email")
                        department = st.selectbox("Department", ["CSE", "IT", "ECE", "EEE"])
                        role = st.selectbox("Role", ["teacher", "class_teacher"])
                        subjects = st.multiselect("Subjects", ["Mathematics", "Physics", "Chemistry", "Computer Science", "Electronics"])
                        password = st.text_input("Initial Password", type="password")
                        
                        if st.form_submit_button("Add Teacher"):
                            add_response = requests.post(
                                f"{API_BASE_URL}/api/admin/users/teachers",
                                headers=headers,
                                json={
                                    "name": name,
                                    "email": email,
                                    "department": department,
                                    "role": role,
                                    "subjects": subjects,
                                    "password": password
                                }
                            )
                            if add_response.status_code == 200:
                                st.success("Teacher added successfully!")
                            else:
                                st.error("Failed to add teacher.")

                # Display and manage existing teachers
                if teachers:
                    st.subheader("Existing Teachers")
                    for teacher in teachers:
                        with st.expander(f"{teacher['name']} ({teacher['email']})"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**Department:** {teacher['department']}")
                                st.write(f"**Role:** {teacher['role']}")
                                st.write(f"**Subjects:** {', '.join(teacher['subjects'])}")
                            with col2:
                                new_role = st.selectbox(
                                    "Change Role",
                                    ["teacher", "class_teacher"],
                                    index=0 if teacher['role'] == 'teacher' else 1,
                                    key=f"role_{teacher['id']}"
                                )
                                if new_role != teacher['role']:
                                    if st.button("Update Role", key=f"update_{teacher['id']}"):
                                        update_response = requests.put(
                                            f"{API_BASE_URL}/api/admin/users/teachers/{teacher['id']}/role",
                                            headers=headers,
                                            json={"role": new_role}
                                        )
                                        if update_response.status_code == 200:
                                            st.success("Role updated successfully!")
                                            st.experimental_rerun()
                                        else:
                                            st.error("Failed to update role.")
                                
                                if st.button("Remove Teacher", key=f"remove_{teacher['id']}"):
                                    if st.checkbox("Confirm deletion?", key=f"confirm_{teacher['id']}"):
                                        delete_response = requests.delete(
                                            f"{API_BASE_URL}/api/admin/users/teachers/{teacher['id']}",
                                            headers=headers
                                        )
                                        if delete_response.status_code == 200:
                                            st.success("Teacher removed successfully!")
                                            st.experimental_rerun()
                                        else:
                                            st.error("Failed to remove teacher.")

        with tab2:
            response = requests.get(f"{API_BASE_URL}/api/admin/users/students", headers=headers)
            if response.status_code == 200:
                students = response.json()
                st.subheader("Students")
                df = pd.DataFrame(students)
                st.dataframe(df)
                
                # Add new student
                with st.expander("Add New Student"):
                    with st.form("add_student"):
                        name = st.text_input("Full Name")
                        email = st.text_input("Email")
                        department = st.selectbox("Department", ["CSE", "IT", "ECE", "EEE"])
                        year = st.selectbox("Year", [1, 2, 3, 4])
                        division = st.selectbox("Division", ["A", "B", "C"])
                        if st.form_submit_button("Add Student"):
                            add_response = requests.post(
                                f"{API_BASE_URL}/api/admin/users/students",
                                headers=headers,
                                json={
                                    "name": name,
                                    "email": email,
                                    "department": department,
                                    "year": year,
                                    "division": division
                                }
                            )
                            if add_response.status_code == 200:
                                st.success("Student added successfully!")
                            else:
                                st.error("Failed to add student.")
        
        with tab3:
            response = requests.get(f"{API_BASE_URL}/api/admin/users/admins", headers=headers)
            if response.status_code == 200:
                admins = response.json()
                st.subheader("Administrators")
                df = pd.DataFrame(admins)
                st.dataframe(df)
                
                # Add new admin
                with st.expander("Add New Administrator"):
                    with st.form("add_admin"):
                        name = st.text_input("Full Name")
                        email = st.text_input("Email")
                        if st.form_submit_button("Add Administrator"):
                            add_response = requests.post(
                                f"{API_BASE_URL}/api/admin/users/admins",
                                headers=headers,
                                json={
                                    "name": name,
                                    "email": email
                                }
                            )
                            if add_response.status_code == 200:
                                st.success("Administrator added successfully!")
                            else:
                                st.error("Failed to add administrator.")
                                
    except Exception as e:
        st.error(f"Error managing users: {str(e)}")

def class_management():
    st.title("Class Management")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get all classes and teachers
        classes_response = requests.get(f"{API_BASE_URL}/api/admin/classes", headers=headers)
        teachers_response = requests.get(f"{API_BASE_URL}/api/admin/users/teachers", headers=headers)
        
        if classes_response.status_code == 200 and teachers_response.status_code == 200:
            classes = classes_response.json()
            teachers = teachers_response.json()
            
            # Create new class
            st.subheader("Create New Class")
            with st.form("create_class"):
                col1, col2 = st.columns(2)
                with col1:
                    class_name = st.text_input("Class Name")
                    department = st.selectbox("Department", ["CSE", "IT", "ECE", "EEE"])
                    year = st.selectbox("Year", [1, 2, 3, 4])
                with col2:
                    division = st.selectbox("Division", ["A", "B", "C"])
                    class_teacher = st.selectbox(
                        "Assign Class Teacher",
                        [f"{t['name']} ({t['email']})" for t in teachers if t['role'] == 'class_teacher']
                    )
                
                if st.form_submit_button("Create Class"):
                    teacher_id = next(t['id'] for t in teachers if f"{t['name']} ({t['email']})" == class_teacher)
                    create_response = requests.post(
                        f"{API_BASE_URL}/api/admin/classes",
                        headers=headers,
                        json={
                            "name": class_name,
                            "department": department,
                            "year": year,
                            "division": division,
                            "class_teacher_id": teacher_id
                        }
                    )
                    if create_response.status_code == 200:
                        st.success("Class created successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to create class.")
            
            # Manage existing classes
            st.subheader("Manage Classes")
            for class_info in classes:
                with st.expander(f"{class_info['name']} - {class_info['department']} Year {class_info['year']} {class_info['division']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("### Class Information")
                        st.write(f"**Department:** {class_info['department']}")
                        st.write(f"**Year:** {class_info['year']}")
                        st.write(f"**Division:** {class_info['division']}")
                        st.write(f"**Class Teacher:** {class_info['class_teacher_name']}")
                    
                    with col2:
                        st.write("### Manage Subjects")
                        new_subject = st.text_input("Add Subject", key=f"subject_{class_info['id']}")
                        subject_teacher = st.selectbox(
                            "Assign Teacher",
                            [f"{t['name']} ({t['email']})" for t in teachers],
                            key=f"teacher_{class_info['id']}"
                        )
                        if st.button("Add Subject", key=f"add_subject_{class_info['id']}"):
                            teacher_id = next(t['id'] for t in teachers if f"{t['name']} ({t['email']})" == subject_teacher)
                            subject_response = requests.post(
                                f"{API_BASE_URL}/api/admin/classes/{class_info['id']}/subjects",
                                headers=headers,
                                json={
                                    "name": new_subject,
                                    "teacher_id": teacher_id
                                }
                            )
                            if subject_response.status_code == 200:
                                st.success("Subject added successfully!")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to add subject.")
                    
                    # Display and manage subjects
                    st.write("### Current Subjects")
                    if 'subjects' in class_info and class_info['subjects']:
                        for subject in class_info['subjects']:
                            col1, col2, col3 = st.columns([3, 2, 1])
                            with col1:
                                st.write(f"**{subject['name']}**")
                            with col2:
                                st.write(f"Teacher: {subject['teacher_name']}")
                            with col3:
                                if st.button("Remove", key=f"remove_subject_{subject['id']}"):
                                    remove_response = requests.delete(
                                        f"{API_BASE_URL}/api/admin/classes/{class_info['id']}/subjects/{subject['id']}",
                                        headers=headers
                                    )
                                    if remove_response.status_code == 200:
                                        st.success("Subject removed successfully!")
                                        st.experimental_rerun()
                                    else:
                                        st.error("Failed to remove subject.")

    except Exception as e:
        st.error(f"Error managing classes: {str(e)}")

def system_reports():
    st.title("System Reports")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Date range selection
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
            
        # Report type selection
        report_type = st.selectbox("Report Type", [
            "Department-wise Attendance",
            "Class-wise Attendance",
            "Teacher-wise Sessions",
            "Daily Attendance Trend"
        ])
        
        # Generate report
        response = requests.get(
            f"{API_BASE_URL}/api/reports/system",
            params={
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "report_type": report_type.lower().replace(" ", "_")
            },
            headers=headers
        )
        
        if response.status_code == 200:
            report_data = response.json()
            
            if report_type == "Department-wise Attendance":
                df = pd.DataFrame(report_data['department_stats'])
                fig = px.bar(df, x='department', y='average_attendance',
                            title='Average Attendance by Department',
                            labels={'average_attendance': 'Average Attendance %'})
                st.plotly_chart(fig)
                
            elif report_type == "Class-wise Attendance":
                df = pd.DataFrame(report_data['class_stats'])
                fig = px.bar(df, x='class_name', y='average_attendance',
                            title='Average Attendance by Class',
                            labels={'average_attendance': 'Average Attendance %'})
                st.plotly_chart(fig)
                
            elif report_type == "Teacher-wise Sessions":
                df = pd.DataFrame(report_data['teacher_stats'])
                fig = px.bar(df, x='teacher_name', y='total_sessions',
                            title='Total Sessions by Teacher')
                st.plotly_chart(fig)
                
            elif report_type == "Daily Attendance Trend":
                df = pd.DataFrame(report_data['daily_trend'])
                df['date'] = pd.to_datetime(df['date'])
                fig = px.line(df, x='date', y='attendance_percentage',
                            title='Daily Attendance Trend',
                            labels={'attendance_percentage': 'Attendance %'})
                st.plotly_chart(fig)
            
            # Download report
            if st.button("Download Report"):
                df.to_csv(f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
                st.success("Report downloaded successfully!")
                
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

def system_settings():
    st.title("System Settings")
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        
        # Get current settings
        response = requests.get(f"{API_BASE_URL}/api/admin/settings", headers=headers)
        
        if response.status_code == 200:
            settings = response.json()
            
            # General Settings
            st.subheader("General Settings")
            with st.form("general_settings"):
                system_name = st.text_input("System Name", value=settings['system_name'])
                attendance_threshold = st.slider("Minimum Attendance Threshold (%)", 
                                              min_value=0, max_value=100, 
                                              value=settings['attendance_threshold'])
                session_timeout = st.number_input("Session Timeout (minutes)", 
                                                min_value=5, max_value=240, 
                                                value=settings['session_timeout'])
                
                if st.form_submit_button("Save General Settings"):
                    update_response = requests.post(
                        f"{API_BASE_URL}/api/admin/settings/general",
                        headers=headers,
                        json={
                            "system_name": system_name,
                            "attendance_threshold": attendance_threshold,
                            "session_timeout": session_timeout
                        }
                    )
                    if update_response.status_code == 200:
                        st.success("Settings updated successfully!")
                    else:
                        st.error("Failed to update settings.")
            
            # Notification Settings
            st.subheader("Notification Settings")
            with st.form("notification_settings"):
                email_notifications = st.checkbox("Enable Email Notifications", 
                                               value=settings['notifications']['email'])
                attendance_alerts = st.checkbox("Send Attendance Alerts", 
                                             value=settings['notifications']['attendance_alerts'])
                low_attendance_warning = st.checkbox("Low Attendance Warnings", 
                                                   value=settings['notifications']['low_attendance_warning'])
                
                if st.form_submit_button("Save Notification Settings"):
                    update_response = requests.post(
                        f"{API_BASE_URL}/api/admin/settings/notifications",
                        headers=headers,
                        json={
                            "email": email_notifications,
                            "attendance_alerts": attendance_alerts,
                            "low_attendance_warning": low_attendance_warning
                        }
                    )
                    if update_response.status_code == 200:
                        st.success("Notification settings updated successfully!")
                    else:
                        st.error("Failed to update notification settings.")
                
    except Exception as e:
        st.error(f"Error managing system settings: {str(e)}")

# Helper functions
def get_teachers():
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/teachers", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def get_subjects():
    try:
        headers = {"Authorization": f"Bearer {get_token()}"}
        response = requests.get(f"{API_BASE_URL}/api/subjects", headers=headers)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def main():
    st.set_page_config(
        page_title="Facial Recognition Attendance System",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar
    with st.sidebar:
        st.title("Navigation")
        if 'token' not in st.session_state:
            st.warning("Please log in to continue")
        else:
            st.success(f"Welcome, {st.session_state['user']['full_name']}")
            
            # Role-specific navigation
            user = get_user()
            role = user['role']
            
            if role == 'student':
                st.subheader("Student Menu")
                page = st.radio("Go to:", 
                    ["Dashboard", "My Attendance", "Mark Attendance", "View Schedule", "Profile"])
            elif role in ['teacher', 'class_teacher']:
                st.subheader("Teacher Menu")
                page = st.radio("Go to:", 
                    ["Dashboard", "Take Attendance", "View Reports", "Manage Classes", "Schedule", "Profile"])
            elif role == 'admin':
                st.subheader("Admin Menu")
                page = st.radio("Go to:", 
                    ["Dashboard", "User Management", "Class Management", "Reports", "System Settings"])
            
            st.button("Logout", on_click=logout)
    
    # Main content
    if 'token' not in st.session_state:
        login()
    else:
        user = get_user()
        role = user['role']
        
        if role == 'student':
            if page == "Dashboard":
                student_dashboard(user['id'])
            elif page == "My Attendance":
                student_attendance(user['id'])
            elif page == "Mark Attendance":
                mark_attendance(user['id'])
            elif page == "View Schedule":
                view_schedule(user['id'])
            elif page == "Profile":
                user_profile(user['id'])
        
        elif role in ['teacher', 'class_teacher']:
            if page == "Dashboard":
                teacher_dashboard(user['id'])
            elif page == "Take Attendance":
                take_attendance(user['id'])
            elif page == "View Reports":
                view_reports(user['id'])
            elif page == "Manage Classes":
                manage_classes(user['id'])
            elif page == "Schedule":
                manage_schedule(user['id'])
            elif page == "Profile":
                user_profile(user['id'])
        
        elif role == 'admin':
            if page == "Dashboard":
                admin_dashboard()
            elif page == "User Management":
                user_management()
            elif page == "Class Management":
                class_management()
            elif page == "Reports":
                system_reports()
            elif page == "System Settings":
                system_settings()
        else:
            st.error("Unknown user role")

if __name__ == "__main__":
    main()
