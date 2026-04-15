from difflib import SequenceMatcher
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template.loader import render_to_string
from PyPDF2 import PdfReader
from xhtml2pdf import pisa


from .forms import ResumeForm
from .models import Resume, Score, Performance

import json



# ================== PDF STATIC FILE HANDLER ==================
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths so xhtml2pdf can access
    static and media files on Render.
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))
    else:
        return uri

    if not os.path.isfile(path):
        raise Exception(f"File not found: {path}")

    return path



# ================== HOME PAGE ==================
def home(request):
    return render(request, 'home.html')

# ================== SIGNUP ==================
def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('signup')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1
        )
        user.save()

        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')

    return render(request, 'signup.html')

# ================== LOGIN ==================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'login.html')


# ================== LOGOUT ==================
def logout_view(request):
    logout(request)
    return redirect('home')


# ================== DASHBOARD ==================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Resume, Score, Performance
import json

@login_required(login_url='/login/')
def dashboard_view(request):
    ats_scores_qs = Score.objects.filter(user=request.user).order_by('submitted_at')
    ats_labels = [s.resume_name for s in ats_scores_qs]
    ats_scores = [float(s.ats_score or 0) for s in ats_scores_qs]

    perf_scores_qs = Performance.objects.filter(user=request.user).order_by('date_taken')
    perf_labels = [p.test_name for p in perf_scores_qs]
    perf_scores = [float(p.score or 0) for p in perf_scores_qs]

    context = {
        'ats_labels': json.dumps(ats_labels),
        'ats_scores': json.dumps(ats_scores),
        'perf_labels': json.dumps(perf_labels),
        'perf_scores': json.dumps(perf_scores),
    }

    return render(request, 'dashboard.html', context)


# ================== RESUME BUILDER ==================
from django.template.loader import render_to_string
from django.http import HttpResponse
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required
from .forms import ResumeForm


@login_required
def resume_builder_view(request):
    if request.method == "POST":
        form = ResumeForm(request.POST)

        if form.is_valid():
            resume = form.save(commit=False)
            resume.user = request.user

            # ✅ Capture ROLE (custom input)
            role = request.POST.get("role", "").strip()

            # Optionally store role in designation field (if desired)
            if role:
                resume.designation = role

            resume.save()

            # ✅ Context for PDF generation
            context = {
                "resume": resume,
                "role": role,

                # ✅ SKILLS
                "programming_languages": (
                    resume.programming_languages.split(",")
                    if resume.programming_languages else []
                ),
                "web_technologies": (
                    resume.web_technologies.split(",")
                    if resume.web_technologies else []
                ),
                "frameworks_tools": (
                    resume.frameworks_tools.split(",")
                    if resume.frameworks_tools else []
                ),
                "database": (
                    resume.database.split(",")
                    if resume.database else []
                ),

                # ✅ EXTRA SECTIONS
                "projects": (
                    resume.projects.splitlines()
                    if resume.projects else []
                ),
                "experience": (
                    resume.experience.splitlines()
                    if resume.experience else []
                ),
                "certifications": (
                    resume.certifications.splitlines()
                    if resume.certifications else []
                ),
                "achievements": (
                    resume.achievements.splitlines()
                    if resume.achievements else []
                ),
            }

            # ✅ Render HTML template
            html = render_to_string("resume_pdf.html", context)

            # ✅ Create PDF using BytesIO
            from io import BytesIO
            result = BytesIO()

            pdf = pisa.pisaDocument(
                BytesIO(html.encode("UTF-8")),
                dest=result,
                encoding="UTF-8",
                link_callback=link_callback
            )

            # ❌ Handle errors
            if pdf.err:
                return HttpResponse(
                    f"PDF generation failed.<br><pre>{html}</pre>",
                    status=500
                )

            # ✅ Return PDF response
            response = HttpResponse(result.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
            return response
    else:
        form = ResumeForm()

    return render(request, "resume_builder.html", {"form": form})
    
# ================== RESUME ANALYZER ==================
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from PyPDF2 import PdfReader
from .models import Score


@login_required
def resume_analyzer_view(request):
    result = None

    # ----------- JOB ROLE KEYWORDS -----------
    JOB_KEYWORDS = {
        "web developer": ["html", "css", "javascript", "django", "react", "git", "api"],
        "python developer": ["python", "django", "flask", "sql", "api", "debugging"],
        "data analyst": ["python", "pandas", "numpy", "excel", "sql", "visualization"],
        "software engineer": ["java", "python", "c++", "oop", "data structures", "algorithms"]
    }

    # ----------- PDF TEXT EXTRACTION -----------
    def extract_text(file):
        try:
            reader = PdfReader(file)
            text = ""
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    text += content
            return text.lower()
        except:
            return ""

    # ----------- ANALYSIS LOGIC -----------
    def analyze(text, role):
        role = role.lower()
        keywords = JOB_KEYWORDS.get(role, [])

        matched = []
        missing = []

        for kw in keywords:
            if kw in text:
                matched.append(kw)
            else:
                missing.append(kw)

        # ✅ KEYWORD SCORE (50)
        keyword_score = int((len(matched) / len(keywords)) * 50) if keywords else 0

        # ✅ SECTION CHECK (30)
        sections = {
            "skills": "skills" in text,
            "projects": "project" in text,
            "education": "education" in text,
            "experience": "experience" in text
        }

        section_score = sum(sections.values()) * 7  # ~28-30

        # ✅ FORMATTING SCORE (20)
        formatting_score = 20 if len(text) > 300 else 10

        total_score = keyword_score + section_score + formatting_score

        # ----------- SUGGESTIONS -----------
        suggestions = []

        if missing:
            suggestions.append("Add missing keywords: " + ", ".join(missing))

        if not sections["skills"]:
            suggestions.append("Include a dedicated Skills section")

        if not sections["experience"]:
            suggestions.append("Add Experience or Internship section")

        if not sections["projects"]:
            suggestions.append("Add Projects with real-world examples")

        if len(text) < 300:
            suggestions.append("Resume content is too short, add more details")

        # ✅ FIXED GITHUB + LINKEDIN CHECK
        if "github.com" not in text and "linkedin.com" not in text:
            suggestions.append("Include GitHub and LinkedIn profile links")
        elif "github.com" not in text:
            suggestions.append("Add your GitHub profile link")
        elif "linkedin.com" not in text:
            suggestions.append("Add your LinkedIn profile link")

        suggestions.append("Use action verbs like Developed, Built, Implemented")
        suggestions.append("Add measurable achievements (e.g. increased performance by 20%)")

        # ----------- CAREER GUIDANCE -----------
        if total_score >= 80:
            guidance = "Excellent ATS-ready resume 🚀 You are ready to apply for top roles."
        elif total_score >= 60:
            guidance = "Good resume 👍 Improve keywords and project details to boost your chances."
        else:
            guidance = "Your resume needs improvement 💡 Focus on skills, projects, and proper structure."

        # ----------- ROLE-BASED GUIDANCE -----------
        role_guidance = {}

        if role == "web developer":
            role_guidance = {
                "roles": ["Frontend Developer", "Backend Developer", "Full Stack Developer"],
                "skills": ["React", "Django", "REST API", "Git"],
            }

        elif role == "python developer":
            role_guidance = {
                "roles": ["Python Developer", "Backend Developer", "Automation Engineer"],
                "skills": ["Django", "Flask", "APIs", "Data Structures"],
            }

        elif role == "software engineer":
            role_guidance = {
                "roles": ["Software Engineer", "Backend Developer", "System Engineer"],
                "skills": ["DSA", "System Design", "OOP", "Git"],
            }

        elif role == "data analyst":
            role_guidance = {
                "roles": ["Data Analyst", "Business Analyst"],
                "skills": ["SQL", "Power BI", "Excel", "Python"],
            }

        return {
            "score": total_score,
            "matched": matched,
            "missing": missing,
            "sections": sections,
            "suggestions": suggestions,
            "guidance": guidance,
            "role": role,
            "role_guidance": role_guidance
        }

    # ----------- HANDLE FORM -----------
    if request.method == "POST":
        pdf = request.FILES.get("resume")
        role = request.POST.get("role")

        if pdf and role:
            text = extract_text(pdf)
            result = analyze(text, role)

            # SAVE SCORE
            if result:
                Score.objects.create(
                    user=request.user,
                    resume_name=pdf.name,
                    ats_score=result['score']
                )

            return render(request, "resume_analyzer.html", {"result": result})

    return render(request, "resume_analyzer.html", {"result": result})

# ================== INTERVIEW PRACTICE ==================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Performance


INTERVIEW_QUESTIONS = {

# ================= WEB DEVELOPER =================
"web developer": [
{"q": "What is HTML?",
 "a": "HTML (HyperText Markup Language) is used to structure content on the web. It defines elements like headings, paragraphs, links, and images, forming the backbone of every webpage."},

{"q": "What is CSS?",
 "a": "CSS (Cascading Style Sheets) is used to style HTML elements. It controls layout, colors, fonts, and responsiveness, making websites visually appealing and user-friendly."},

{"q": "What is JavaScript?",
 "a": "JavaScript is a programming language used to make web pages interactive. It handles events, updates content dynamically, and communicates with servers using APIs."},

{"q": "What is responsive design?",
 "a": "Responsive design ensures that a website adapts to different screen sizes like mobile, tablet, and desktop using flexible layouts and media queries."},

{"q": "What is the DOM?",
 "a": "The DOM is a structured representation of an HTML document that allows JavaScript to access and modify elements dynamically."},

{"q": "Difference between GET and POST?",
 "a": "GET sends data through the URL and is less secure, while POST sends data in the request body and is more secure, commonly used for form submissions."},

{"q": "What is an API?",
 "a": "An API allows communication between different software systems, enabling data exchange between frontend and backend."},

{"q": "What is Git?",
 "a": "Git is a version control system used to track code changes, collaborate with teams, and manage project history."},

{"q": "What is Bootstrap?",
 "a": "Bootstrap is a CSS framework used to build responsive and mobile-first websites quickly using pre-designed components."},

{"q": "What is Django?",
 "a": "Django is a Python web framework used to build secure and scalable web applications efficiently."},
],


# ================= PYTHON DEVELOPER =================
"python developer": [
{"q": "What is Python?",
 "a": "Python is a high-level, interpreted programming language known for its simplicity, readability, and wide range of applications."},

{"q": "What are Python data types?",
 "a": "Python has built-in data types like int, float, string, list, tuple, dictionary, and set used to store different kinds of data."},

{"q": "What is list comprehension?",
 "a": "List comprehension is a concise way to create lists using a single line of code with loops and conditions."},

{"q": "What is a dictionary?",
 "a": "A dictionary is a collection of key-value pairs used for fast data retrieval."},

{"q": "What is OOP?",
 "a": "Object-Oriented Programming organizes code using classes and objects, improving reusability and structure."},

{"q": "What is exception handling?",
 "a": "Exception handling manages runtime errors using try, except, and finally blocks to prevent program crashes."},

{"q": "What is Django?",
 "a": "Django is a high-level Python framework used to develop web applications quickly and securely."},

{"q": "What is Flask?",
 "a": "Flask is a lightweight Python web framework used for building simple applications."},

{"q": "What is NumPy?",
 "a": "NumPy is a library used for numerical computing and working with arrays."},

{"q": "What is Pandas?",
 "a": "Pandas is a library used for data manipulation and analysis using data structures like DataFrames."},
],


# ================= SOFTWARE ENGINEER =================
"software engineer": [
{"q": "What is software engineering?",
 "a": "Software engineering is the process of designing, developing, testing, and maintaining software systems using engineering principles."},

{"q": "What is SDLC?",
 "a": "SDLC is a structured process including planning, designing, developing, testing, and deploying software."},

{"q": "What is Agile?",
 "a": "Agile is a development approach that focuses on iterative progress, collaboration, and flexibility."},

{"q": "What is version control?",
 "a": "Version control tracks changes in code and helps teams collaborate effectively."},

{"q": "What are design patterns?",
 "a": "Design patterns are reusable solutions to common software design problems."},

{"q": "What is REST API?",
 "a": "REST API is a web service that uses HTTP methods to enable communication between systems."},

{"q": "What is testing?",
 "a": "Testing is the process of identifying bugs and ensuring software quality."},

{"q": "What is debugging?",
 "a": "Debugging is the process of finding and fixing errors in code."},

{"q": "What is normalization?",
 "a": "Normalization organizes database data to reduce redundancy and improve efficiency."},

{"q": "What is scalability?",
 "a": "Scalability is the ability of a system to handle increased workload efficiently."},
],


# ================= DATA ANALYST =================
"data analyst": [
{"q": "What is data analysis?",
 "a": "Data analysis is the process of examining data to extract insights and support decision-making."},

{"q": "What is SQL?",
 "a": "SQL is a language used to manage and query relational databases."},

{"q": "What is Excel?",
 "a": "Excel is a tool used for data analysis, calculations, and visualization."},

{"q": "What is data visualization?",
 "a": "Data visualization represents data using charts and graphs for better understanding."},

{"q": "What is Pandas?",
 "a": "Pandas is a Python library used for data analysis and manipulation."},

{"q": "What is NumPy?",
 "a": "NumPy is used for numerical operations and array handling."},

{"q": "What is KPI?",
 "a": "KPI is a measurable value used to evaluate performance."},

{"q": "What is correlation?",
 "a": "Correlation measures the relationship between two variables."},

{"q": "What is data cleaning?",
 "a": "Data cleaning involves removing errors and inconsistencies from data."},

{"q": "What is dashboard?",
 "a": "A dashboard visually presents important data and insights."},
],


# ================= HR =================
"hr interview": [
{"q": "Tell me about yourself.",
 "a": "I am a motivated individual with a background in computer science, skilled in programming and problem-solving, and eager to grow in a professional environment."},

{"q": "What are your strengths?",
 "a": "My strengths include problem-solving, quick learning, and strong communication skills."},

{"q": "What are your weaknesses?",
 "a": "I sometimes focus too much on details, but I am improving by managing time effectively."},

{"q": "Why should we hire you?",
 "a": "I bring strong technical skills, a learning mindset, and the ability to contribute effectively to your team."},

{"q": "Where do you see yourself in 5 years?",
 "a": "I see myself growing into a skilled professional, contributing to impactful projects and taking more responsibilities."},

{"q": "Why do you want this job?",
 "a": "I am interested in this role because it aligns with my skills and career goals."},

{"q": "What motivates you?",
 "a": "I am motivated by learning new things and solving challenging problems."},

{"q": "How do you handle stress?",
 "a": "I handle stress by staying organized, prioritizing tasks, and maintaining a calm approach."},

{"q": "Describe a challenge you faced.",
 "a": "I faced a challenge in a project where I resolved issues by analyzing problems step by step and collaborating with teammates."},

{"q": "Are you a team player?",
 "a": "Yes, I work well in teams and believe collaboration leads to better results."},
]
}

# ================== VIEW ==================
@login_required
def interview_practice_view(request):

    context = {
        "questions": None,
        "learn_mode": False,
        "finished": False,
        "role": None,
        "results": None,
        "total_score": None,
        "max_score": None
    }

    # ================= GET REQUEST =================
    if request.method == "GET":
        return render(request, "interview_practice.html", context)

    # ================= POST REQUEST =================
    if request.method == "POST":

        # ---------- START TEST ----------
        if "start_test" in request.POST:

            role = request.POST.get("role", "").lower()
            questions = INTERVIEW_QUESTIONS.get(role, [])

            request.session["questions"] = questions
            request.session["role"] = role

            context.update({
                "questions": questions,
                "role": role,
                "learn_mode": False
            })

            return render(request, "interview_practice.html", context)

        # ---------- LEARN MODE ----------
        elif "learn_mode" in request.POST:

            role = request.POST.get("role", "").lower()
            questions = INTERVIEW_QUESTIONS.get(role, [])

            context.update({
                "questions": questions,
                "role": role,
                "learn_mode": True
            })

            return render(request, "interview_practice.html", context)

        # ---------- SUBMIT TEST ----------
        elif "submit_test" in request.POST:

            questions = request.session.get("questions", [])
            role = request.session.get("role", "")

            results = []
            total_score = 0
            max_score = len(questions) * 10

            for i, q in enumerate(questions):

                user_answer = request.POST.get(f"answer_{i}", "").strip().lower()
                correct_answer = q["a"].strip().lower()

                similarity = SequenceMatcher(None, user_answer, correct_answer).ratio()

                if similarity >= 0.85:
                    score = 10
                elif similarity >= 0.5:
                    score = 5
                else:
                    score = 0

                total_score += score

                results.append({
                    "question": q["q"],
                    "user": user_answer,
                    "correct": q["a"],
                    "score": score
                })

            # Save in database
            Performance.objects.create(
                user=request.user,
                test_name=role,
                score=total_score
            )

            return render(request, "interview_practice.html", {
                "questions": questions,
                "results": results,
                "total_score": total_score,
                "max_score": max_score,
                "role": role,
                "finished": True,
                "learn_mode": False
            })
            
# ================== SETTINGS ==================
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .forms import CustomPasswordChangeForm


@login_required
def settings_view(request):
    """
    Settings page displaying user profile information.
    """
    return render(request, 'settings.html', {
        'user': request.user
    })


@login_required
def edit_profile(request):
    """
    Edit user profile information.
    """
    if request.method == 'POST':
        user = request.user

        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('user_settings')

    return render(request, 'edit_profile.html', {
        'user': request.user
    })


@login_required
def change_password(request):
    """
    Allow users to change their password securely.
    """
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keeps user logged in
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('user_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'password_change.html', {'form': form})


@login_required
def toggle_theme(request):
    """
    Toggle between light and dark themes using session storage.
    """
    current_theme = request.session.get("theme", "light")
    request.session["theme"] = "dark" if current_theme == "light" else "light"

    return redirect(request.META.get("HTTP_REFERER", "/"))