import asyncio
from services.score_calculator import calculate_final_score
from services.keyword_engine import compute_keyword_score
from services.semantic_engine import compute_semantic_score
from services.experience_engine import compute_experience_score
from services.impact_detector import compute_impact_score

resume_text = """Nikhil Kumar B
Hyderabad, Telangana, India
+91 98765 43210
nikhilkumarb.dev@gmail.com
LinkedIn: linkedin.com/in/nikhilkumarb
GitHub: github.com/nikhilkumarb

PYTHON DEVELOPER

PROFESSIONAL SUMMARY
Results-driven Python Developer with strong expertise in designing, developing, and deploying scalable enterprise applications, leveraging expertise in Python, Java, Spring Boot, Microservices, REST APIs, SQL, and cloud deployment, with experience in building high-performance backend systems, optimizing application performance, and leading development initiatives in Agile environments.

TECHNICAL SKILLS
Programming Languages: Java, Python, SQL, JavaScript
Frameworks: Spring Boot, Spring MVC, Spring Security, Hibernate, JPA
Databases: MySQL, PostgreSQL, MongoDB
Tools & Technologies: Git, Docker, Apache Maven, Jenkins, Amazon Web Services, Python
Architecture: Microservices, REST APIs, Distributed Systems, Event-Driven Architecture
Relevant Knowledge & Exposure: Confluence, Box, DCIM Tools, ServiceNow, AWS, Cloud infrastructure

PROFESSIONAL EXPERIENCE
**Senior Java Developer** -- Infosys | Hyderabad, India | July 2023 – Present
- Developed scalable microservices using Spring Boot serving over 500K+ users, applying principles of REST APIs and Microservices architecture.
- Designed and implemented secure REST APIs, integrating with AWS and leveraging Python for data processing.
- Improved application performance by 40% through query optimization and applied Event-Driven Architecture principles.
- Implemented JWT authentication and authorization, utilizing Python for automation scripts.
- Integrated third-party payment and notification services, working with ServiceNow and Box integrations.
- Led a team of 4 developers in Agile sprint delivery, ensuring production-quality code and documentation.

**Java Developer** -- Tata Consultancy Services | Bangalore, India | June 2022 – June 2023
- Developed backend modules using Java and Spring Boot, applying principles of Microservices and REST APIs.
- Built CRUD APIs for enterprise applications, leveraging Python for data analysis and optimization.
- Worked with MySQL database optimization, designing and implementing scalable database solutions.
- Created unit tests with JUnit and utilized Python for automation testing.
- Fixed production bugs and improved code quality, ensuring Confluence and DCIM Tools integrations.

**Associate Software Engineer** -- Cognizant | Chennai, India | May 2021 – May 2022
- Developed Java modules for banking applications, integrating with Box and applying principles of Event-Driven Architecture.
- Worked on API integrations, utilizing Python for data processing and AWS for cloud deployment.
- Created SQL stored procedures and applied principles of Distributed Systems.
- Participated in code reviews, ensuring adherence to ServiceNow and AWS best practices.

PROJECTS
**Digital Banking Platform** -- Tech Stack: Java, Spring Boot, MySQL, Docker, Python
- Developed secure transaction APIs, applying principles of REST APIs and Microservices architecture.
- Implemented role-based access, utilizing Python for automation scripts and Box for content management.
- Processed 100K+ transactions/day, ensuring integration with ServiceNow and AWS.

**E-Commerce Order Management System** -- Tech Stack: Java, Microservices, MongoDB, Python
- Built order and inventory services, applying principles of Event-Driven Architecture and Distributed Systems.
- Integrated payment gateway, utilizing Python for data processing and AWS for cloud deployment.
- Designed event-driven communication, ensuring integration with Confluence and DCIM Tools.

EDUCATION
**Bachelor of Technology in Computer Science** -- SRM Institute of Science and Technology | 2017 – 2021

CERTIFICATIONS
- Oracle Certified Java Programmer
- AWS Cloud Practitioner

SOFT SKILLS
- Leadership
- Problem Solving
- Communication
- Team Collaboration
- Critical Thinking"""

jd_text = """
We are looking for a Python Developer with experience in building backend services.
Required Skills: Python, REST APIs, SQL, AWS, Microservices, Docker, Git.
Preferred Skills: Java, Spring Boot, MongoDB, PostgreSQL, CI/CD, Agile.
Must have 3+ years of experience.
"""

resume_skills = ["Java", "Python", "SQL", "JavaScript", "Spring Boot", "Spring MVC", "Spring Security", "Hibernate", "JPA", "MySQL", "PostgreSQL", "MongoDB", "Git", "Docker", "Apache Maven", "Jenkins", "Amazon Web Services", "Microservices", "REST APIs", "Distributed Systems", "Event-Driven Architecture", "Confluence", "Box", "DCIM Tools", "ServiceNow", "AWS"]
required_skills = ["Python", "REST APIs", "SQL", "AWS", "Microservices", "Docker", "Git"]
preferred_skills = ["Java", "Spring Boot", "MongoDB", "PostgreSQL", "CI/CD", "Agile"]
jd_role = "Python Developer"
jd_years = 3

keyword_res = compute_keyword_score(resume_skills, resume_text, required_skills, preferred_skills)
semantic_score = compute_semantic_score(resume_text, jd_text)
experience_res = compute_experience_score(
    resume_text=resume_text,
    employment_dates=[
        {"start_date": "July 2023", "end_date": "Present", "title": "Senior Java Developer"},
        {"start_date": "June 2022", "end_date": "June 2023", "title": "Java Developer"},
        {"start_date": "May 2021", "end_date": "May 2022", "title": "Associate Software Engineer"}
    ],
    years_mentioned=[],
    min_required_years=jd_years
)
impact_score = compute_impact_score(resume_text).get("score", 0)

final = calculate_final_score(semantic_score, keyword_res["score"], experience_res["score"], impact_score, resume_text)

print("Keyword Score:", keyword_res["score"])
print("Semantic Score:", semantic_score)
print("Experience Score:", experience_res["score"])
print("Impact Score:", impact_score)
print("FINAL SCORE:", final["ats_score"])
print("Stuffing flags:", keyword_res["stuffing_flags"])
