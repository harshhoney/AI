# take resume in pdf or word
# have hr give you a list of things like skill, experience, projects
# extract these from resume
# match against the hr list
# generate a percentage of matching score

import os
import fitz
from dotenv import load_dotenv
from groq import Groq
from docx import Document
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
from pypdf import PdfReader
import json
import time


# def extract_text(file_path):
#     file_path = Path(file_path)
#     extension = file_path.suffix.lower()
#     extracted_text = ""
#     if extension == ".pdf":

#         doc = fitz.open(file_path)

#         # print("Total pages:", len(doc))

#         for page_number, page in enumerate(doc):

#             text = page.get_text()

#             # print(f"\nPage {page_number + 1}")
#             # print("Extracted characters:", len(text))
#             # print("Extracted content:", repr(text))

#             extracted_text += text + "\n"

#         doc.close()
#     elif extension == '.docx':
#         doc = Document(file_path)
#         for paragraph in doc.paragraphs:
#             extracted_text += paragraph.text + '\n'
#     else:
#         raise ValueError("Unsupported file format")
#     return extracted_text


def read_pdf(file_path):
    reader = PdfReader(file_path)
    text=""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def read_docx(file_path):
    document = Document(file_path)
    text = ""
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text += paragraph.text + "\n"

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    text += cell.text + "\n"
    return text

def read_resume(file_path):
    if file_path.suffix.lower() == ".pdf":
        return read_pdf(file_path)
    elif file_path.suffix.lower() == ".docx":
        return read_docx(file_path)
    else : 
        return ""

def parse_resume(resume_text):
    system_prompt = f"""
    You are an expert resume parser.

    Extract information from the resume based on its meaning,
    not only based one exact section headings.

    Different resumes may use different headings.

    For example:
    - Experience
    - Professional Experience
    - Work History
    - Employment
    - Internships

    These may all contain relevant experience.

    Skill my also appear in the skills section,, work experience,
    internships or projects.

    Return only valid Json matchin this schema:

    {resume_schema}

    Important rules:

    1. Do not invent information.
    2. If a value is not available, return null.
    3. If a list has no information, return an empty list.
    4. Include internships inside experiences.
    5. Extract skills mentioned across the entire resume.
    """

    user_prompt = f"""
    Parse the following resume
    {resume_text}
    """

    message_system = {
        "role" : "system",
        "content" : system_prompt
    }

    message_user = {
        "role" : "user",
        "content" : user_prompt
    }

    messages = [ message_system,message_user]
    response_format = {
        "type" : "json_object"
    }

    response = client.chat.completions.create(model = model,messages = messages,response_format = response_format)
    raw_output = response.choices[0].message.content
    data = json.loads(raw_output)
    resume = Resume(**data)
    return resume

load_dotenv()
my_api_key=os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("API kye kaha hai bhai")

client = Groq(api_key = my_api_key)
model="openai/gpt-oss-120b"


job_description = """
Description
The Everyday Essentials Experience Org delivers a world-class shopping experience for everyday essentials that is efficient, habitual, and economical for customers and selling partners. We are looking for a Software Development Engineer with strong ownership and a drive to solve complex, large-scale problems through creative solutions.

The Everyday Essential Cost to Serve team drives multi-million dollar cost savings for Amazon through its multipack programs. The team owns how Amazon represents, prices, and fulfills multipack products worldwide, and is currently executing a ground-up re-architecture of the multipack platform as a leadership-priority initiative, promoting multipacks to first-class purchasable products. This work changes how millions of customers discover, purchase, and receive multipacks, and how selling partners manage their multipack catalog.

What makes this role unique is the breadth. Your work will span the entire retail funnel: ASIN creation, catalog ingestion, pricing determination, selection and ranking, and customer-facing experiences on Search, Detail Page, Cart, Checkout,
and the multipacks storefront. You will work closely with the science team and have the opportunity to develop and influence the models that drive multipack selection and personalization. Few teams at Amazon offer this combination of
end-to-end systems exposure.

You will build systems that separate what a customer buys from how it is fulfilled, enabling seamless multipack experiences from online multipacks fulfilled with individual units to physical products shipped as a single item. You will have the freedom to experiment, propose new multipack experiences, and ship them worldwide. Your ideas move from whiteboard to production, visible to hundreds of millions of customers. You will shape foundational decisions in an active re-architecture program with high visibility to senior leadership

Key job responsibilities
Design, build, and own end-to-end software solutions that are scalable, reliable, and maintainable across the full software development lifecycle.
Collaborate with product managers, principal engineers, and cross-functional teams to translate business requirements into technical designs and working software.
Drive continuous improvement by identifying gaps in existing systems, proposing solutions, and delivering results with a high bar for quality and operational excellence.
Participate actively in code reviews, contribute to team best practices, and mentor junior engineers to raise the technical bar across the team.
Operate with a good sense of ownership — monitoring systems you build, responding to operational issues, and iterating quickly to improve customer and partner experience.

Basic Qualifications
- 3+ years of non-internship professional software development experience
- 2+ years of non-internship design or architecture (design patterns, reliability and scaling) of new and existing systems experience
- Experience programming with at least one software programming language
- Bachelor's degree in computer science or equivalent

Preferred Qualifications
- 3+ years of full software development life cycle, including coding standards, code reviews, source control management, build processes, testing, and operations experience
"""

class JobD(BaseModel):
    role : str
    required_skills: list[str]
    preferred_skills : list[str]
    minimum_experience: Optional[float] = None
    education_requirements : list[str]
    responsibilites : list[str]

jobd_schema = JobD.model_json_schema()

system_prompt = f"""
You are an expert HR assistant.

Your job is to analyze job descriptions and extract structured infromation from them.
Return only valid json matching this schema.
{jobd_schema}

IMPORTANT:
Do Not return the schema itself.
Do Not return fields like "properties", "title" or "type".
Fill the schema with actual information extracted from the job description.

if minimum experience is not mentioned, return null.
if information for a list is missing, return an empty list.
Do not invent information.
"""

user_prompt = f"""
Analyze the following job description:

{job_description}
"""

message_system = {
    "role" : "system",
    "content" : system_prompt
}

message_user = {
    "role" : "user",
    "content": user_prompt
}

response_format = {
    "type" : "json_object"
}

messages = [message_system,message_user]

response = client.chat.completions.create(model = model,messages = messages, response_format = response_format)

answer = response.choices[0].message.content

raw_json = answer

job_data = json.loads(raw_json)
job = JobD(**job_data)

print(job.minimum_experience)
print(job.education_requirements)

class MatchResult(BaseModel):
    score : float
    details : dict

class Experience(BaseModel):
    company : Optional[str] = None
    role : Optional[str] = None
    duration : Optional[str] = None
    description : Optional[str] = None
    skills_used: list[str] = []


class Resume(BaseModel):
    name : Optional[str] = None
    email : Optional[str] = None
    phone : Optional[str] = None
    total_experience_years: Optional[float] = None
    skills: list[str] = []
    experiences : list[Experience] = []
    education : list[str] = []
    projects: list[str] = []
    certifications : list[str] = []

resume_schema = Resume.model_json_schema()

def final_score(job,resume):
    match_schema = MatchResult.model_json_schema()
    prompt = f"""
    You are an HR recruiter.

    Compare the candidate's resume with the job description.

    JOB DESCRIPTION:
    {job.model_dump_json(indent =2)}

    CANDIDATE RESUME:
    {resume.model_dump_json(indent=2)}
    Return json matching this schema:
    {match_schema}

    Give me :

    1. Candiate name
    2. Matching skills
    3. Missing important skills
    4. Whether experience requirement is met
    5. Overall match percentage is met
    6. A short final verdict

    Keep the response concise and easy to read.
    """

    message = {
        "role" : "user",
        "content" : prompt
    }

    messages = [message]
    response_format = {
        "type" : "json_object"
    }

    response = client.chat.completions.create(model=model,messages = messages,response_format = response_format)
    data = json.loads(response.choices[0].message.content)
    return MatchResult(**data)

resume_folder = Path("resumes")
all_results=[]
for file_path in resume_folder.iterdir():
    if file_path.suffix.lower() not in [".pdf",".docx"]:
        continue
    print("\nProcessing: ", file_path.name)
    resume_text = read_resume(file_path)
    parsed_resume = parse_resume(resume_text)
    time.sleep(5)
    result = final_score(job,parsed_resume)
    time.sleep(5)
    print("Score", result.score)
    all_results.append({
        "name" : parsed_resume.name,
        "score" : result.score,
        "details" : result.details
    })

all_results.sort(
    key=lambda candidate : candidate["score"],
    reverse=True
)

top_2 = all_results[:2]
worst_2 = all_results[-2:]

print("TOP 2 CANDIDATES")
for candidate in top_2:
    print(
        candidate["name"],
        "-",
        candidate["score"],
        "%"
    )
    print(candidate["details"])

print("LOWEST 2 CANDIDATES")
for candidate in worst_2:
    print(
        candidate["name"],
        "-",
        candidate["score"],
        "%"
    )
    print(candidate["details"])


# class JobInfo(BaseModel):
#     experience : str
#     skill : str
#     projects : str

# qualificationsNeeded  = JobInfo(
#     experience = "2 years",
#     skill = "Android Developement",
#     projects = "Need projects using Kotlin or Java"
# )    

# schema = JobInfo.model_json_schema()
# response_format={
#     "type" : "json_object"
# }

# system_prompt = f"""
# Extract the information based on this schema and give me a json output.
# {schema}
# """

# system_message = {
#     "role" : "system",
#     "content" : system_prompt
# }

# resume_details = extract_text(r"C:\Users\Lenovo\Downloads\Harsh_Kumar_Resume.pdf")
# # print(resume_details)

# user_prompt = f"""
# This is resume details , please extract the details from this.
# {resume_details}
# """
# user_message = {
#     "role" : "user",
#     "content" : user_prompt
# }

# messages = [system_message,user_message]

# response = client.chat.completions.create(model = model,messages = messages,response_format = response_format)
# answer = response.choices[0].message.content
# print(answer)

# import json 
# raw_json = answer
# data_file = json.loads(raw_json)
# candidateQualifications = JobInfo(**data_file)



# compare_candidate_eligible_percentage_prompt = f"""
#  now compare the required qualifications and the candidate qualifications and tell me in percentage how much is this candiate 
#  eligible for the role.
#  required qualifications for the role -> {qualificationsNeeded}
#  candidate qualications for the role -> {candidateQualifications}
# """

# match_percentage_message = {
#     "role" : "user",
#     "content" : compare_candidate_eligible_percentage_prompt
# }

# list = [match_percentage_message]
# resp = client.chat.completions.create(model = model,messages = list)
# ans = resp.choices[0].message.content

# print(ans)