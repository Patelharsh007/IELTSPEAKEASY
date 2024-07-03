#Importing the necessary libraries
import time
import json
from datetime import datetime  
from flask import Flask, jsonify, make_response, request, session, render_template,url_for,redirect,flash
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from flask_cors import CORS
from werkzeug.security import generate_password_hash,check_password_hash
from models.user import User,Admin
from models.intro import Part1Question
from models.quecard import Part2CueCard
from models.response import Response
from models.analysis import Analysis
import os
from bson import ObjectId
from functools import wraps
import pandas as pd
from flask_socketio import SocketIO, emit

import google.generativeai as genai
import os

# Load the environment variables from the .env file
load_dotenv()

# Configure the Gemini API key
api_key= os.getenv("GOOGLE_API_KEY")
#genai.configure(api_key=api_key)
genai.api_key = os.getenv("GOOGLE_API_KEY")
model = genai.GenerativeModel('gemini-1.0-pro-latest')

#Creating the Flask app
app = Flask(__name__)



#Setting up the MongoDB URI
app.config['MONGO_URI'] = os.getenv("MONGO_URL")

# Set the secret key for session management
app.secret_key = os.getenv("SECRET_KEY")

#Creating the PyMongo instance
mongo = PyMongo(app)

# Enable Cross Origin Resource Sharing
CORS(app)

# Initialize Flask-SocketIO
socketio = SocketIO(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Where to redirect for login

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    user_data = User.get_by_id(mongo, user_id)
    if user_data:
        return User(user_data['username'], user_data['email'], user_data['password_hash'], user_data['role'], user_data['_id'])
    return None



# Check if the database connection was successful
try:
    mongo.db.command('ping')  # Attempt to ping the database
    print("Connected to the database successfully!")
except Exception as e:
    print("Failed to connect to the database:", e)


#Creating a route to test the Flask app
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/app')
def app_page():
    return render_template('base.html')

#Creating a route to register a new user
@app.route('/admin/register', methods=['GET', 'POST'])
def register_admin():
    if request.method == 'POST':
        # Get registration data from request body
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if username or email already exists
        existing_user = Admin.get_by_username_or_email(mongo, username, email)
        if existing_user:
            return jsonify({"error": "Username or email already exists"}), 400

        # Create a new User instance
        new_user = Admin(username=username, email=email, password=password)

        # Save the new user to the database
        new_user.save(mongo)

        return jsonify({"message": "Admin registered successfully", "user_id": str(new_user.id)}), 201
    
    # If the request method is GET, render the registration form
    return render_template('admin_register.html')



#Creating a route to register a new user
@app.route('/user/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Get registration data from request body
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        # Check if username or email already exists
        existing_user = User.get_by_username_or_email(mongo, username, email)
        if existing_user:
            return jsonify({"error": "Username or email already exists"}), 400

        # Create a new User instance
        new_user = User(username=username, email=email, password=password)

        # Save the new user to the database
        new_user.save(mongo)

        return jsonify({"message": "User registered successfully", "user_id": str(new_user.id)}), 201
    
    # If the request method is GET, render the registration form
    return render_template('register.html')

#Creating a route to login a user
@app.route('/login', methods=['GET', 'POST'])
def login_user_route():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user_data = User.get_by_username(mongo, username)
        # print(user_data)
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['username'], user_data['email'], user_data['password_hash'], user_data['role'], user_data['_id'])
            print({user.role}, {user.username})

            login_user(user)
            return jsonify({"message": f"{user.role}: {user.username} Logged in successfully"}), 200

        return jsonify({"error": "Invalid username or password"}), 401

    return render_template('login.html')

@app.route('/logout')
@login_required  # Protect the logout route
def logout():
    logout_user()
    return redirect(url_for('index'))

# Creating a route to view an active user profile
@app.route('/profile')
@login_required
def profile():
    user = current_user
    return render_template('profile.html', user=user)

# Creating a route to update the username
@app.route('/update-username', methods=['POST'])
@login_required
def update_username():
    new_username = request.form.get('username')
    current_user_username = current_user.username

    # Check if the new username is already in use
    existing_user = mongo.db.users.find_one({'username': new_username})

    if new_username == current_user_username:
        flash("Same username entered.", "error")
        return redirect(url_for('profile'))

    if existing_user:
        flash("Username already in use. Please choose a different one.", "error")
        return redirect(url_for('profile'))

    if new_username:
        mongo.db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$set': {'username': new_username}})
        flash("Username changed successfully", "success")
        return redirect(url_for('profile'))
    else:
        flash("New username is required", "error")
        return redirect(url_for('profile'))

# Creating a route to update the email
@app.route('/update-email', methods=['POST'])
@login_required
def update_email():
    new_email = request.form.get('email')
    current_user_email = current_user.email

    # Check if the new email is already in use
    existing_user = mongo.db.users.find_one({'email': new_email})

    if new_email == current_user_email:
        flash("Same email entered.", "error")
        return redirect(url_for('profile'))

    if existing_user:
        flash("Email already in use. Please choose a different one.", "error")
        return redirect(url_for('profile'))

    if new_email:
        mongo.db.users.update_one({'_id': ObjectId(current_user.get_id())}, {'$set': {'email': new_email}})
        flash("Email changed successfully", "success")
        return redirect(url_for('profile'))
    else:
        flash("New email is required", "error")
        return redirect(url_for('profile'))

# Creating a route to update the password
@app.route('/update-password', methods=['GET', 'POST'])
@login_required
def update_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user_id = current_user.get_id()
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

        if not user or not check_password_hash(user['password_hash'], current_password):
            flash("Current password is incorrect", "error")
            return redirect(url_for('profile'))

        if new_password != confirm_password:
            flash("New password and confirm password do not match", "error")
            return redirect(url_for('profile'))

        # Update the password
        hashed_password = generate_password_hash(new_password)
        mongo.db.users.update_one({'_id': ObjectId(user_id)}, {'$set': {'password_hash': hashed_password}})
        
        flash("Password updated successfully", "success")
        return redirect(url_for('profile'))

    return render_template('profile.html')

# Ensure that admin access is required for these routes
def admin_required(f):
    @login_required
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.role != 'admin':
            flash("Admin access required", "error")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrap

#admin dashboard
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    if current_user.role != 'admin':
        return jsonify({"error": "Unauthorized access"}), 403
    
    users = User.get_all_users(mongo)
    admins = User.get_all_admins(mongo)

    return render_template('admin_dash.html', users=users,admins=admins)

# Edit user route
@app.route('/admin/user/<user_id>/edit', methods=['POST'])
@admin_required
def edit_user(user_id):
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')

        if mongo.db.users.find_one({'username': username, '_id': {'$ne': ObjectId(user_id)}}):
            flash("Username already in use", "error")
            return redirect(url_for('users'))

        if mongo.db.users.find_one({'email': email, '_id': {'$ne': ObjectId(user_id)}}):
            flash("Email already in use", "error")
            return redirect(url_for('users'))

        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'username': username, 'email': email, 'role': role}}
        )
        flash("User updated successfully", "success")
    return redirect(url_for('users'))

# Delete user route
@app.route('/admin/user/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    flash("User deleted successfully", "success")
    return redirect(url_for('users'))

# Edit admin route
@app.route('/admin/admin/<user_id>/edit', methods=['POST'])
@admin_required
def edit_admin(user_id):
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')

        if mongo.db.users.find_one({'username': username, '_id': {'$ne': ObjectId(user_id)}}):
            flash("Username already in use", "error")
            return redirect(url_for('admins'))

        if mongo.db.users.find_one({'email': email, '_id': {'$ne': ObjectId(user_id)}}):
            flash("Email already in use", "error")
            return redirect(url_for('admins'))

        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {'username': username, 'email': email, 'role': role}}
        )
        flash("Admin updated successfully", "success")
    return redirect(url_for('admins'))

# Delete user route
@app.route('/admin/admin/<user_id>/delete', methods=['POST'])
@admin_required
def delete_admin(user_id):
    mongo.db.users.delete_one({'_id': ObjectId(user_id)})
    flash("Admin deleted successfully", "success")
    return redirect(url_for('admins'))

#user info
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    if request.method == 'GET':    
        users= User.get_all_users(mongo)
        return render_template('admin_users.html', users=users,active='users')
    
    return render_template('admin_users.html',active='View Users')

#get admins info
@app.route('/admin/admins', methods=['GET', 'POST'])
@login_required
@admin_required
def admins():
    if request.method == 'GET':    
        admins = User.get_all_admins(mongo)
        return render_template('admin_admins.html',admins=admins,active='admins')
    
    return render_template('admin_admins.html',active='View Users')

#upload csv page
@app.route('/admin/upload-csv',methods=['GET'])
@login_required
@admin_required
def upload_csv():
    if request.method=="GET":
        return render_template('upload_csv.html')

#upload intro questions
@app.route('/admin/upload-part1', methods=['POST','GET'])
@login_required
@admin_required
def upload_part1():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
                error_occurred = False
                
                for index, row in df.iterrows():
                    try:
                        category = row['Category']
                        question = row['Question']
                        part1_question = Part1Question(category=category, question=question)
                        part1_question.save(mongo)
                    except Exception as e:
                        error_occurred = True
                        flash(f'Error processing row {index + 1}: {str(e)}', 'danger')
                        continue
                
                if not error_occurred:
                    flash('Part 1 questions uploaded successfully!', 'success')
                else:
                    flash('Part 1 questions uploaded with some errors.', 'warning')
            
            except Exception as e:
                flash(f'Error reading the file: {str(e)}', 'danger')
        else:
            flash('Invalid file format. Please upload a CSV file.', 'danger')

        return redirect(url_for('upload_csv'))
        
    return render_template('upload_csv.html', active='part1')


#upload quecards
@app.route('/admin/upload-part2', methods=['POST','GET'])
@login_required
@admin_required
def upload_part2():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and file.filename.endswith('.csv'):
            try:
                df = pd.read_csv(file)
                for index, row in df.iterrows():
                    cue_card = row['CueCard']
                    points = row['Points']
                    mongo.db.part2_cue_cards.insert_one({'cue_card': cue_card, 'points': points})
                flash('Part 2 cue cards uploaded successfully!', 'success')
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'danger')
        else:
            flash('Invalid file format. Please upload a CSV file.', 'danger')
    return redirect(url_for('upload_csv'))

#display questions for admin
@app.route('/admin/display-questions')
@login_required
def display_questions_admin():
    part1_questions = Part1Question.get_all(mongo)
    part2_cue_cards = Part2CueCard.get_all(mongo)
    
    return render_template('admin_display_questions.html', part1_questions=part1_questions, part2_cue_cards=part2_cue_cards)

#display questions for users
@app.route('/user/display-questions')
@login_required
def display_questions_users():
    part1_questions = Part1Question.get_all(mongo)
    part2_cue_cards = Part2CueCard.get_all(mongo)
    
    return render_template('user_display_questions.html', part1_questions=part1_questions, part2_cue_cards=part2_cue_cards)


#user dashboard:
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    
    return render_template('user_dash.html')


#Start exam
@app.route('/user/exam', methods=['GET'])
@login_required
def exam():
    return render_template('exam.html')


@app.route('/user/exam/basic', methods=['GET', 'POST'])
@login_required
def basic_questions():
    if request.method == 'POST':
        user_id = current_user._id
        session_id = request.form.get('session_id')

        basic_questions_responses = []
        for i in range(1, 5):  # Adjust based on the number of questions
            question = request.form.get(f'question-{i}')
            response = request.form.get(f'response-{i}')
            basic_questions_responses.append({"question": question, "response": response})

        # Save or update the response in the database
        response = Response(
            user_id=user_id,
            exam_session_id=session_id,
            basic_questions=basic_questions_responses
        )
        response.save(mongo)

        # Redirect to the Part 1 questions section with the session ID
        return redirect(url_for('part1', session_id=session_id))
    
    # If GET request, render the basic questions template
    basic_questions = [
        "May I know your full name?",
        "How may I address you?",
        "May I see your ID?",
        "Where do you come from?"
    ]
    return render_template('basic_questions.html', basic_questions=basic_questions)


@app.route('/user/exam/part1', methods=['GET', 'POST'])
@login_required
def part1():
    if request.method == 'POST':
        user_id = current_user._id
        session_id = request.form.get('session_id')
        part1_questions_responses = []

        for key in request.form:
            if key.startswith('response-'):
                question_id = key.split('-')[1]
                question_text = request.form.get(f'question-{question_id}')
                response_text = request.form.get(key)
                part1_questions_responses.append({"question": question_text, "response": response_text})
        
        # Fetch existing response if it exists
        existing_response = Response.get_by_session_id(mongo, session_id)
        
        if existing_response:
            existing_response.part1_questions = part1_questions_responses
            mongo.db.responses.update_one(
                {'_id': existing_response._id},
                {'$set': {'part1_questions': part1_questions_responses}}
            )
        else:
            # Create a new response object if it doesn't exist
            response = Response(
                user_id=user_id,
                exam_session_id=session_id,
                part1_questions=part1_questions_responses
            )
            response.save(mongo)

        # Redirect to Part 2 with session_id as query parameter
        return redirect(url_for('part2', session_id=session_id))
    
    # If GET request, retrieve questions for Part 1
    session_id = request.args.get('session_id')
    questions = Part1Question.get_random_questions_from_categories(mongo)
    questions_data = [question.to_dict() for question in questions]
    return render_template('part1.html', questions=questions_data, session_id=session_id)


# Part 2: Cue Card
# Part 2: Cue Card
@app.route('/user/exam/part2', methods=['GET', 'POST'])
@login_required
def part2():
    if request.method == 'POST':
        user_id = current_user._id
        session_id = request.form.get('session_id')
        cue_card_question = request.form.get('cue_card_question')
        response_text = request.form.get('response')

        existing_response = Response.get_by_session_id(mongo, session_id)

        if existing_response:
            existing_response.part2_cue_card = {
                'cue_card': cue_card_question,
                'response': response_text
            }
            mongo.db.responses.update_one(
                {'_id': existing_response._id},
                {'$set': existing_response.to_dict()}
            )
        else:
            response = Response(
                user_id=user_id,
                exam_session_id=session_id,
                part2_cue_card={
                    'question': cue_card_question,
                    'response': response_text
                }
            )
            response.save(mongo)

        return redirect(url_for('part3', session_id=session_id))

    session_id = request.args.get('session_id')
    cue_card = Part2CueCard.get_random_cue_card(mongo)
    return render_template('part2.html', cue_card=cue_card, session_id=session_id)

#part3 follow up
# Part 3: Follow-up Questions
@app.route('/user/exam/part3', methods=['GET', 'POST'])
def part3():
    if request.method == 'GET':
        session_id = request.args.get('session_id')
        response_record = Response.get_by_session_id(mongo, session_id)

        if response_record and response_record.part2_cue_card:
            user_response = response_record.part2_cue_card.get('response')
            cue_card_question = response_record.part2_cue_card.get('cue_card')

            # Use Google Gemini to generate follow-up questions based on user response
            try:
                model = genai.GenerativeModel('gemini-1.0-pro-latest')
                prompt = (f"Based on the following IELTS speaking cue card question and the user's response, "
                          f"generate follow-up questions to test the user's English speaking skills:\n\n"
                          f"Question: {cue_card_question}\n\n"
                          f"Response: {user_response}\n\n"
                          f"Generate the follow-up questions below:")                
                result = model.generate_content(prompt)
                follow_up_questions = result.text.split('\n')
                # Remove asterisks and other markdown formatting
                follow_up_questions = [q.replace('*', '').strip() for q in follow_up_questions if q.strip()]
                print("follow:",follow_up_questions)
                #follow_up_questions=follow_up_questions[1:]

            except Exception as e:
                print(f"Failed to generate follow-up questions: {str(e)}")
                follow_up_questions = ["Could you elaborate on that?", "Can you provide more details?"]

            return render_template('part3.html', session_id=session_id, part3_questions=follow_up_questions)

        return "No part 2 response found for this session.", 404

    if request.method == 'POST':
        session_id = request.form.get('session_id')
        follow_up_questions = request.form.getlist('follow_up_questions')
        responses = request.form.getlist('responses')

        response_record = Response.get_by_session_id(mongo, session_id)

        if response_record:
            part3_data = list(zip(follow_up_questions, responses))
            response_record.part3_answers.extend(part3_data)
            mongo.db.responses.update_one(
                {'_id': response_record._id},
                {'$set': response_record.to_dict()}
            )
        

        return redirect(url_for('evaluate_exam', session_id=session_id))
    

@app.route('/user/exam/evaluate')
def evaluate_exam():
    try:
        session_id = request.args.get('session_id')
        response_record = Response.get_by_session_id(mongo, session_id)

        if not response_record:
            return "Response record not found.", 404

        criteria = ["fluency and coherence", "lexical resource", "grammatical range and accuracy", "pronunciation"]
        model = genai.GenerativeModel('gemini-1.0-pro-latest')

        scores = {
            'part1': {},
            'part2': {},
            'part3': {}
        }
        band_scores = {
            'part1': 0,
            'part2': 0,
            'part3': 0,
            'overall': 0
        }
        overall_evaluation = ''

        # # Evaluate Basic Questions
        # if response_record.basic_questions:
        #     basic_prompt = (
        #         f"Evaluate the following responses based on the criteria for IELTS speaking test.\n"
        #         f"Responses: {response_record.basic_questions}\n"
        #         f"Criteria: {', '.join(criteria)}\n"
        #         f"Band Score: "
        #     )
        #     basic_result = model.generate_content(basic_prompt)
        #     scores['basic'] = basic_result.text
        #     band_scores['basic'] = evaluate_to_band_score(response_record.basic_questions,criteria)
        #     band_scores['basic']=float(band_scores['basic'])
        #     print(band_scores['basic'])

        # Evaluate Part 1 Questions
        if response_record.part1_questions:
            part1_prompt = (
                f"Evaluate the following responses based on the criteria for IELTS speaking test.\n"
                f"Responses: {response_record.part1_questions}\n"
                f"Criteria: {', '.join(criteria)}\n"
                f"Band Score: "
            )
            part1_result = model.generate_content(part1_prompt)
            scores['part1'] = part1_result.text
            band_scores['part1'] = evaluate_to_band_score(response_record.part1_questions,criteria)
            band_scores['part1']=float(band_scores['part1'])
            print(band_scores['part1'])

        # Evaluate Part 2 Cue Card
        if response_record.part2_cue_card:
            part2_response = response_record.part2_cue_card.get('response', '')
            if part2_response:
                part2_prompt = (
                    f"Evaluate the following response based on the criteria for IELTS speaking test.\n"
                    f"Response: {part2_response}\n"
                    f"Criteria: {', '.join(criteria)}\n"
                    f"Band Score: "
                )
                part2_result = model.generate_content(part2_prompt)
                scores['part2'] = part2_result.text
                

                print(part2_result)
                band_scores['part2'] = evaluate_to_band_score(part2_response,criteria)
                band_scores['part2']=float(band_scores['part2'])
                print(band_scores['part2'])

        # Evaluate Part 3 Answers
        if response_record.part3_answers:
            part3_responses = [answer for answer in response_record.part3_answers]
            pt=[answer[1] for answer in response_record.part3_answers if answer[1]]
            if part3_responses:
                part3_prompt = (
                    f"Evaluate the following responses based on the criteria for IELTS speaking test.\n"
                    f"Responses: {part3_responses}\n"
                    f"Criteria: {', '.join(criteria)}\n"
                    f"Band Score: "
                )

                part3_result = model.generate_content(part3_prompt)
                scores['part3'] = part3_result.text
                band_scores['part3'] = evaluate_to_band_score(pt,criteria)
                band_scores['part3']=float(band_scores['part3'])
                print(band_scores['part3'])

        addn=band_scores['part1']+band_scores['part2']+band_scores['part3']

        # Calculate Overall Evaluation
        overall_score = addn/3
        overall_band = float(overall_score)  # Convert overall score to integer band score

        # Example: Assigning overall_evaluation based on overall_band
        if overall_band >= 7:
            overall_evaluation = "Very good performance."
        elif overall_band >= 5:
            overall_evaluation = "Good performance."
        else:
            overall_evaluation = "Needs improvement."

        # Save Evaluation Results
        response_record.scores = scores
        response_record.band_scores = band_scores
        response_record.overall_evaluation = overall_evaluation
        # response_record.overall_band = overall_band
        response_record.save(mongo)

        return render_template('exam_results.html', 
                               scores=scores, 
                               band_scores=band_scores, 
                               overall_evaluation=overall_evaluation,
                               overall_band=overall_band)
    
    except Exception as e:
        return str(e), 500
   
def evaluate_to_band_score(response,criteria):
    prompt = f"Evaluate the response:\n{response} based on {criteria} and give score in the range of 0-9 as in ielts exams but rember you only have to return the output as Band Score:score and no any comment or anything yes or no not single thing and score according if empty recived"
    model = genai.GenerativeModel('gemini-1.0-pro-latest')
    result = model.generate_content(prompt)
    
    # Extract band score from the result
    lines = result.text.splitlines()
    for line in lines:
        if line.startswith("Band Score:"):
            try:
                band_score =(line.split(":")[1].strip())
                return band_score
            except ValueError:
                pass  # Handle cases where band score is not an integer or not found
    
    return float(0)  # Default to 0 if band score is not found or can't be extracted




if __name__ == '__main__':
    app.run(debug=True)