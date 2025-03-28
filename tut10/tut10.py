import streamlit as st
import pandas as pd
from io import BytesIO

# Function to process the uploaded file
def process_file(file):
    # Read the uploaded file into a DataFrame
    df = pd.read_excel(file)

    # Get number of exams, max marks row, weightage row, and student details
    number_of_exams = len(df.columns) - 2
    max_marks_row = df.iloc[0]
    weightage_row = df.iloc[1]
    student_df = df.iloc[2:].copy().reset_index(drop=True)
    student_df['Grand Total'] = 0

    # Calculate Grand Total for each student
    number_of_students = len(student_df)
    for i in range(number_of_students):
        val = 0
        for j in range(number_of_exams):
            val += student_df.iloc[i, j + 2] / max_marks_row[j + 2] * weightage_row[j + 2]
        student_df.at[i, 'Grand Total'] = val
    student_df = student_df.sort_values(by='Grand Total', ascending=False).reset_index(drop=True)

    # Define grade cutoffs
    grade_cutoffs = {
        'AA': int(number_of_students * 0.05),
        'AB': int(number_of_students * 0.15),
        'BB': int(number_of_students * 0.25),
        'BC': int(number_of_students * 0.30),
        'CC': int(number_of_students * 0.15),
        'CD': int(number_of_students * 0.05)
    }
    remaining = number_of_students - sum(grade_cutoffs.values())

    # Assign grades
    grades = (
        ['AA'] * grade_cutoffs['AA'] +
        ['AB'] * grade_cutoffs['AB'] +
        ['BB'] * grade_cutoffs['BB'] +
        ['BC'] * grade_cutoffs['BC'] +
        ['CC'] * grade_cutoffs['CC'] +
        ['CD'] * grade_cutoffs['CD'] +
        ['DD'] * remaining
    )
    student_df['Grade'] = grades

    # Calculate grade-wise stats
    grade_stats = student_df.groupby('Grade')['Grand Total'].agg(['count', 'min', 'max']).reset_index()
    grade_stats.rename(columns={'count': 'Count', 'min': 'Min (x)', 'max': 'Max (x)'}, inplace=True)

    # Add empty rows for grades without students (e.g., F, I, PP, NP)
    for grade in ['F', 'I', 'PP', 'NP']:
        if grade not in grade_stats['Grade'].values:
            grade_stats = pd.concat([grade_stats, pd.DataFrame({'Grade': [grade], 'Count': [0], 'Min (x)': [None], 'Max (x)': [None]})], ignore_index=True)

    # Sort grades in the desired order
    grade_order = ['AA', 'AB', 'BB', 'BC', 'CC', 'CD', 'DD', 'F', 'I', 'PP', 'NP']
    grade_stats['Grade'] = pd.Categorical(grade_stats['Grade'], categories=grade_order, ordered=True)
    grade_stats = grade_stats.sort_values('Grade').reset_index(drop=True)

    # Sort by Roll number for output_roll
    sorted_roll = student_df.sort_values(by='Roll', ascending=True)

    # Convert DataFrames to Excel files in memory
    output1 = BytesIO()
    output2 = BytesIO()
    student_df.to_excel(output1, index=False, engine='openpyxl')
    sorted_roll.to_excel(output2, index=False, engine='openpyxl')
    output1.seek(0)
    output2.seek(0)

    return output1, output2, grade_stats

# Streamlit app layout and functionality
st.title("Excel Grading App")

st.write("Upload an Excel file with student scores to calculate 'Grand Total' and assign grades. The app will generate two output Excel files and a grade statistics table based on your data.")

uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")

if uploaded_file is not None:
    # Process the uploaded file and generate outputs
    output1, output2, grade_stats = process_file(uploaded_file)

    # Display the grade statistics table
    st.write("### Grade Statistics Table")
    st.dataframe(grade_stats)

    # Provide download links for the two output files
    st.download_button(
        label="Download Grand Total and Grades",
        data=output1,
        file_name="output_grades.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="Download Sorted by Roll",
        data=output2,
        file_name="output_roll.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
