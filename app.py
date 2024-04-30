from flask import Flask, request, render_template, redirect, url_for, flash
import csv
import random
from ast import literal_eval
import os

app = Flask(__name__)

app.secret_key = os.urandom(24)


def distribute_questions(total_marks, faculty_count, part_marks, remaining_marks_per_question):
    allocated_questions = [[] for _ in range(faculty_count)]

    # Ensure at least one question for each faculty
    for faculty in range(faculty_count):
        allocated_questions[faculty].append(1)  # Allocate 1 question for Part A
        total_marks -= part_marks[faculty][0]

    # Randomly select a faculty for Part A questions if more than one faculty
    if faculty_count > 1:
        part_a_faculty = random.randint(0, faculty_count - 1)
    else:
        part_a_faculty = 0
    # Calculate faculty capacity, considering any remaining marks
    faculty_capacity = total_marks // faculty_count
    remaining_marks = total_marks % faculty_count

    if not all(remaining_marks_per_question):
        return "Error: Ensure there are enough questions for distribution."

    # Create a list of remaining questions
    remaining_questions = list(range(1, len(remaining_marks_per_question)))

    for faculty in range(faculty_count):
        if not remaining_questions:
            break

        if faculty == part_a_faculty:
            continue

        faculty_question = remaining_questions.pop(0)
        allocated_questions[faculty].append(faculty_question)
        total_marks -= remaining_marks_per_question[faculty]

        num_questions = faculty_capacity

        if remaining_marks > 0:
            num_questions += 1
            remaining_marks -= 1

        num_questions = min(num_questions, len(remaining_questions))

        if num_questions > 0:
            allocated_questions[faculty].extend(remaining_questions[:num_questions])
            total_marks -= num_questions
            remaining_questions = remaining_questions[num_questions:]

    return allocated_questions

@app.route('/', methods=['GET', 'POST'])
def exam_form():
    if request.method == 'POST':
        num_courses = int(request.form['numCourses'])
        course_data = []
        for i in range(1, num_courses + 1):
            data = [
                request.form.get(f'programName{i}', 'Not Found'),
                request.form.get(f'year{i}', 'Not Found'),
                request.form.get(f'semester{i}', 'Not Found'),
                request.form.get(f'courseName{i}', 'Not Found'),
                int(request.form.get(f'facultyCount{i}', 0)),
                request.form.get(f'facultyNames{i}', 'Not Found'),
                request.form.get(f'eventName{i}', 'Not Found'),
                int(request.form.get(f'totalMarks{i}', 0)
            )
            ]
            # Extract and split faculty names
            faculty_names = request.form.get(f'facultyNames{i}', 'Not Found').split(",")
            faculty_count = len(faculty_names)

            if faculty_count <= 0:
                flash("Faculty count must be greater than zero")
                return redirect(url_for('exam_form'))

            part_marks = [
                [
                    int(request.form.get(f'partAQuestions{i}_{faculty}', 0)),
                    int(request.form.get(f'partBQuestions{i}_{faculty}', 0)),
                    int(request.form.get(f'partCQuestions{i}_{faculty}', 0))
                ]
                for faculty in range(faculty_count)
            ]

            remaining_marks_per_question = [sum(part) for part in zip(*part_marks)]

            if len(data) >= 9:
                allocated_questions = distribute_questions(data[8], faculty_count, part_marks, remaining_marks_per_question)
                course_data.append(data + [part_marks] + allocated_questions)
        try :
             with open('exam_data.csv', 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile)
                csvwriter.writerow(course_data)
        except Exception as e:
              flash(f"An error occurred while writing to the CSV file: {str(e)}")        
            
        return redirect(url_for('response_page', course_data=course_data))

    return render_template('exam_form.html')

@app.route('/response', methods=['GET'])
def response_page():
    file_path = 'C:\\Users\\pvjay\\OneDrive\\Desktop\\project-2\\exam_data.csv'
    try:
        with open(file_path, 'r', newline='') as csvfile:
            csvreader = csv.reader(csvfile)
            course_data = [row for row in csvreader]

        # Modify the course data to the expected format (if needed)
        for row in course_data:
            row[11:] = [literal_eval(q_str) for q_str in row[11:]]

        return render_template('response.html', course_data=course_data)
    except Exception as e:
        flash(f"An error occurred while reading the CSV file: {str(e)}")

    # Handle the case where there was an error reading the CSV
    return redirect(url_for('exam_form'))
    
if __name__ == '__main__':
    app.run(debug=True)
    
