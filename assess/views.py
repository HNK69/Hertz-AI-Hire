
from os import path
import subprocess, tempfile, textwrap

from accounts import views
from ml_service.question_gen import get_questions_for_skills
from accounts.models import CandidateProfile
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

from accounts.models import CandidateProfile
from .models import TestSubmission, ResultReport
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required
from accounts.models import CandidateProfile
from ml_service.hr_evaluator import evaluate_hr_answer

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CandidateProfile
from .models import TestSubmission, ResultReport

# import parser
from ml_service.resume_parser import parse_resume

def has_submitted(candidate, test_type):
    """Check if user already submitted this test."""
    from .models import TestSubmission
    return TestSubmission.objects.filter(candidate=candidate, test_type=test_type).exists()


@login_required
def dashboard(request):
    profile = get_object_or_404(CandidateProfile, user=request.user)
    submissions = TestSubmission.objects.filter(candidate=request.user).order_by("-submitted_at")
    return render(request, "assess/dashboard.html", {"profile": profile, "submissions": submissions})

# assess/views.py (partial - only upload_resume view)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CandidateProfile
from .models import TestSubmission, ResultReport

from ml_service.resume_parser import parse_resume
from ml_service.project_extractor import extract_projects_from_text

@login_required
def upload_resume(request):
    profile, _ = CandidateProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        f = request.FILES.get("resume")
        if f:
            profile.resume = f
            profile.current_stage = "resume"
            profile.save()
            try:
                res = parse_resume(profile.resume.path)
                profile.resume_text = res.get("text", "")[:100000]
                profile.skills = res.get("skills", [])
                profile.embedding = res.get("embedding", [])
                # new: extract projects and save
                projects = extract_projects_from_text(profile.resume_text)
                profile.projects = projects
                profile.save()
                messages.success(
                    request,
                    "Resume uploaded and parsed. Skills detected: " + ", ".join(profile.skills or ["(none)"])
                    + (". Projects found: " + ", ".join(projects) if projects else "")
                )
            except Exception as e:
                messages.warning(request, f"Resume uploaded but parsing failed: {e}")
            return redirect("assess:dashboard")
    return render(request, "assess/upload_resume.html", {"profile": profile})


@login_required
def tech_interview(request):
    profile = get_object_or_404(CandidateProfile, user=request.user)
    if request.method == "POST":
        transcript = request.POST.get("transcript", "")
        score = round(random.uniform(0.5, 0.9), 3)
        TestSubmission.objects.create(candidate=request.user, test_type="tech", answers={"transcript": transcript}, score=score)
        profile.current_stage = "hr"
        profile.save()
        messages.success(request, f"Tech interview finished. Score: {score}")
        return redirect("assess:hr_interview")
    return render(request, "assess/tech_interview.html", {"profile": profile})

@login_required
def hr_interview(request):
    profile = get_object_or_404(CandidateProfile, user=request.user)
    if request.method == "POST":
        transcript = request.POST.get("transcript", "")
        score = round(random.uniform(0.5, 0.95), 3)
        TestSubmission.objects.create(candidate=request.user, test_type="hr", answers={"transcript": transcript}, score=score)
        # decide final outcome based on random
        decision = "offered" if random.random() > 0.35 else "rejected"
        profile.current_stage = "done"
        profile.status = "offered" if decision == "offered" else "rejected"
        profile.save()
        rr = ResultReport.objects.create(candidate=request.user, report_text=f"Final decision: {decision}", decision=decision)
        messages.success(request, f"HR done. Decision: {decision}")
        return redirect("assess:result")
    return render(request, "assess/hr_interview.html", {"profile": profile})

@login_required
def wait_page(request):
    profile = get_object_or_404(CandidateProfile, user=request.user)
    return render(request, "assess/wait.html", {"profile": profile})


@login_required
def final_result(request):
    """Display final interview outcome."""
    try:
        profile = CandidateProfile.objects.get(user=request.user)
    except CandidateProfile.DoesNotExist:
        return render(request, "assess/result.html", {
            "error": "Candidate profile not found."
        })

    test_scores = TestSubmission.objects.filter(candidate=request.user)

    aptitude = coding = tech = hr = 0
    for t in test_scores:
        if t.test_type == "aptitude":
            aptitude = t.score
        elif t.test_type == "coding":
            coding = t.score
        elif t.test_type == "tech":
            tech = t.score
        elif t.test_type == "hr":
            hr = t.score

    decision = profile.status
    feedback = (
        "Excellent performance across all rounds!"
        if decision in ["shortlisted", "offered"]
        else "Thank you for participating. Keep improving — you're close!"
    )

    return render(
        request,
        "assess/result.html",
        {
            "profile": profile,
            "aptitude": round(aptitude * 100 if aptitude <= 1 else aptitude, 1),
            "coding": round(coding * 100 if coding <= 1 else coding, 1),
            "tech": round(tech * 100 if tech <= 1 else tech, 1),
            "hr": round(hr, 2),
            "decision": decision,
            "feedback": feedback,
        },
    )

@login_required
def aptitude_test(request):
    profile = get_object_or_404(CandidateProfile, user=request.user)
    if has_submitted(request.user, "aptitude"):
        messages.warning(request, "You have already completed the Aptitude Test.")
        return redirect("assess:dashboard")

    from assess.models import Question
    questions = list(Question.objects.order_by("?")[:15])

    if not questions:
        from ml_service.question_gen import import_questions_from_csv
        import_questions_from_csv()
        questions = list(Question.objects.order_by("?")[:15])

    print("🧠 DEBUG QUESTIONS:", len(questions))
    for q in questions[:3]:
        print("•", q.text[:100])

    

    if request.method == "POST":
        answers = {}
        correct = 0
        total = len(questions)

        for q in questions:
            key = f"q_{q.id}"
            ans = request.POST.get(key)
            answers[str(q.id)] = ans
            if ans == str(q.correct_index):
                correct += 1

        score = round(correct / max(total, 1), 4)


        TestSubmission.objects.create(
            candidate=request.user,
            test_type="aptitude",
            answers=answers,
            score=score,
        )
        profile.current_stage = "coding"
        profile.save()
        messages.success(request, f"Aptitude test submitted. Score: {round(score * 100, 2)}% ({correct}/{total})")

        return redirect("assess:coding_test")

    return render(request, "assess/aptitude.html", {"questions": questions, "profile": profile})


from ml_service.code_question_gen import get_three_coding_questions
import subprocess, tempfile

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
import subprocess, tempfile

from django.contrib import messages
import subprocess, tempfile, json
from accounts.models import CandidateProfile
from .models import TestSubmission


  # adjust import if needed


@login_required
def coding_test(request):
    import os, statistics, json, tempfile, subprocess
    from pathlib import Path
    from accounts.models import CandidateProfile
    from .models import TestSubmission
    from ml_service.code_question_gen import get_three_coding_questions
    if has_submitted(request.user, "coding"):
        messages.warning(request, "You have already completed the Coding Test.")
        return redirect("assess:dashboard")


    def analyze_code_quality(code):
        """Run pylint + radon and return combined quality score (0–1)."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        try:
            pylint_proc = subprocess.run(
                ["pylint", tmp_path, "--disable=all", "--enable=E,W,C,R", "-f", "json"],
                capture_output=True, text=True, timeout=10
            )
            pylint_output = pylint_proc.stdout.strip()
            pylint_penalties = len(json.loads(pylint_output)) if pylint_output else 0
            pylint_score = max(0, 1 - (pylint_penalties / 20))

            radon_proc = subprocess.run(
                ["radon", "cc", "-j", tmp_path],
                capture_output=True, text=True, timeout=10
            )
            radon_data = json.loads(radon_proc.stdout or "{}")
            comp_scores = []
            for fn_list in radon_data.values():
                for fn in fn_list:
                    rank = fn.get("rank", "F")
                    mapping = {"A": 1.0, "B": 0.9, "C": 0.75, "D": 0.5, "E": 0.3, "F": 0.1}
                    comp_scores.append(mapping.get(rank, 0.5))
            radon_score = statistics.mean(comp_scores) if comp_scores else 0.7

            return round(0.7 * pylint_score + 0.3 * radon_score, 2)
        except Exception as e:
            print("⚠️ Code quality analysis failed:", e)
            return 0.5
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    # -------------------------------------------------------------
    profile = CandidateProfile.objects.get(user=request.user)
    questions = get_three_coding_questions(profile.skills or [])
    results = []

    if request.method == "POST":
        total_score = 0

        for q in questions:
            code = request.POST.get(f"code_{q.id}", "")
            passed = 0

            # Parse test cases
            test_cases = q.test_cases if q.test_cases else []
            if not isinstance(test_cases, list):
                try:
                    test_cases = json.loads(test_cases)
                except Exception:
                    test_cases = []

            total = len(test_cases)
            if total == 0:
                results.append({"title": q.title, "score": 0})
                continue

            for case in test_cases:
                inp = case.get("input", "")
                expected = str(case.get("output", "")).strip()
                output = ""
                stderr = ""

                try:
                    # write candidate code to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as tmp:
                        tmp.write(code)
                        tmp.flush()

                        # 1️⃣ normal script run (for input()/print())
                        run = subprocess.run(
                            ["python", tmp.name],
                            input=inp.encode(),
                            capture_output=True,
                            timeout=3
                        )
                        output = run.stdout.decode().strip()
                        stderr = run.stderr.decode().strip()

                    # 2️⃣ fallback: try solve()
                    if not output:
                        runner = f"""
import json, sys
from importlib.machinery import SourceFileLoader
mod = SourceFileLoader("candidate", r"{tmp.name}").load_module()
data = sys.stdin.read().strip()
try:
    parsed = list(map(int, data.split()))
except Exception:
    parsed = data.splitlines() if "\\n" in data else data
res = mod.solve(parsed)
if res is not None:
    try:
        print(json.dumps(res))
    except Exception:
        print(res)
"""
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8") as r:
                            r.write(runner)
                            r.flush()
                            run = subprocess.run(
                                ["python", r.name],
                                input=inp.encode(),
                                capture_output=True,
                                timeout=3
                            )
                            output = run.stdout.decode().strip()
                            stderr += "\n" + run.stderr.decode().strip()

                    # normalize and compare
                    match = False
                    if output == expected:
                        match = True
                    else:
                        try:
                            if float(output) == float(expected):
                                match = True
                        except Exception:
                            pass
                        if not match:
                            try:
                                match = json.loads(output) == json.loads(expected)
                            except Exception:
                                pass

                    if match:
                        passed += 1
                    else:
                        print(f"[❌] Failed | input: {repr(inp)} | expected: {repr(expected)} | got: {repr(output)} | stderr: {stderr}")

                except subprocess.TimeoutExpired:
                    print(f"[⏰] Timeout for input: {inp}")
                except Exception as e:
                    print(f"[🔥] Runtime error: {e}")
                finally:
                    if os.path.exists(tmp.name):
                        os.remove(tmp.name)
                    try:
                        os.remove(r.name)
                    except Exception:
                        pass

            # combine with code quality
            test_score = round(passed / total, 4) if total else 0
            code_quality = analyze_code_quality(code)
            score = round((test_score * 0.7) + (code_quality * 0.3), 4)

            total_score += score
            results.append({
                "title": q.title,
                "test_score": round(test_score * 100, 2),
                "code_quality": round(code_quality * 100, 2),
                "final_score": round(score * 100, 2)
            })

        avg_score = round(total_score / len(questions), 4) if questions else 0

        TestSubmission.objects.create(
            candidate=request.user,
            test_type="coding",
            answers={"results": results},
            score=avg_score,
        )

        profile.current_stage = "tech"
        profile.save()

        messages.success(request, f"Coding Test Completed. Avg Score: {round(avg_score * 100, 2)}%")
        return redirect("assess:tech_interview")

    return render(request, "assess/coding_test.html", {"questions": questions})



@login_required
def coding_result(request):
    submissions = TestSubmission.objects.filter(candidate=request.user, test_type="coding")
    total_score = round(sum(s.score for s in submissions[-3:]) / min(len(submissions[-3:]), 3), 2)
    return render(request, "assess/coding_result.html", {"submissions": submissions[-3:], "total_score": total_score})

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def tech_interview_page(request):
    return render(request, "tech_interview.html")


# assess/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from ml_service.tech_interview_engine import generate_tech_questions
from accounts.models import CandidateProfile


@login_required
def get_tech_questions(request):
    """
    API endpoint to return generated tech interview questions
    based on the candidate's resume data.
    """
    profile = CandidateProfile.objects.get(user=request.user)
    skills = profile.skills or []
    projects = profile.projects or []

    questions = generate_tech_questions(skills, projects)
    return JsonResponse({"questions": questions})
# assess/views.py
from ml_service.tech_evaluator import evaluate_tech_answer
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def submit_tech_interview(request):
    import traceback
    from django.http import JsonResponse
    import json

    if has_submitted(request.user, "tech"):
        messages.warning(request, "You have already completed the HR Interview.")
        return redirect("assess:dashboard")




    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            transcript = data.get("transcript", [])
            print("🔹 TECH TRANSCRIPT RECEIVED:", transcript)

            if not transcript:
                return JsonResponse({"error": "Empty transcript"}, status=400)

            # calculate average score
            total_score = 0
            for entry in transcript:
                ans = entry.get("a", "")
                total_score += evaluate_tech_answer(ans)

            avg_score = round(total_score / max(1, len(transcript)), 2)

            # update profile + record submission
            profile = CandidateProfile.objects.get(user=request.user)
            TestSubmission.objects.create(
                candidate=request.user,
                test_type="tech",
                answers={"transcript": transcript},
                score=avg_score / 5,  # normalize 0–1 for DB consistency
            )

            profile.current_stage = "hr"
            profile.save()

            print(f"✅ Tech interview saved for {profile.user.username} — Score: {avg_score}")
            return JsonResponse({"avg_score": avg_score, "status": "moved_to_hr"})

        except Exception as e:
            print("🔥 Tech Submit Error:", str(e))
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)

from ml_service.hr_interview_engine import generate_hr_questions

@login_required
def hr_interview_page(request):
    """Renders HR interview chatbot page"""
    return render(request, "assess/hr_interview.html")


@login_required
def get_hr_questions(request):
    """API endpoint for HR interview questions"""
    questions = generate_hr_questions()
    return JsonResponse({"questions": questions})
from ml_service.hr_evaluator import evaluate_hr_answer
import json

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def submit_hr_interview(request):
    import traceback
    from django.http import JsonResponse
    import json
    if has_submitted(request.user, "hr"):
        messages.warning(request, "You have already completed the HR Interview.")
        return redirect("assess:dashboard")


    if request.method == "POST":
        try:
            raw = request.body.decode("utf-8")
            print("🔹 RAW REQUEST BODY:", raw)  # <-- watch this in terminal

            data = json.loads(raw)
            transcript = data.get("transcript", [])
            print("🔹 TRANSCRIPT RECEIVED:", transcript)

            if not transcript:
                return JsonResponse({"error": "Empty transcript"}, status=400)

            total_score = 0
            for entry in transcript:
                ans = entry.get("a", "")
                total_score += evaluate_hr_answer(ans)

            avg_score = round(total_score / max(1, len(transcript)), 2)

            profile = CandidateProfile.objects.get(user=request.user)
            profile.current_stage = "done"
            profile.status = "shortlisted" if avg_score >= 3.5 else "rejected"
            profile.save()

            print(f"✅ HR interview saved for {profile.user.username} — Score: {avg_score}")
            return JsonResponse({"avg_score": avg_score, "status": profile.status})

        except Exception as e:
            print("🔥 HR Submit Error:", str(e))
            traceback.print_exc()
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def rejection_report(request):
    profile = get_object_or_404(CandidateProfile, user=request.user)
    try:
        report = ResultReport.objects.filter(candidate=request.user, decision="rejected").latest("created_at")
    except ResultReport.DoesNotExist:
        report = None

    # Fetch round-wise scores
    tests = TestSubmission.objects.filter(candidate=request.user)
    aptitude = coding = tech = hr = 0
    for t in tests:
        if t.test_type == "aptitude":
            aptitude = t.score
        elif t.test_type == "coding":
            coding = t.score
        elif t.test_type == "tech":
            tech = t.score
        elif t.test_type == "hr":
            hr = t.score

    # Simple reason synthesis
    reasons = []
    if aptitude < 0.6:
        reasons.append("Aptitude performance was below the cutoff.")
    if coding < 0.6:
        reasons.append("Coding test score did not meet expectations.")
    if tech < 0.6:
        reasons.append("Technical interview lacked sufficient depth.")
    if hr < 3.0:
        reasons.append("HR evaluation indicated areas for communication or attitude improvement.")

    if not reasons:
        reasons = ["Overall performance was competitive, but other candidates performed slightly better."]

    return render(
        request,
        "assess/rejection.html",
        {
            "profile": profile,
            "report": report,
            "aptitude": round(aptitude * 100 if aptitude <= 1 else aptitude, 1),
            "coding": round(coding * 100 if coding <= 1 else coding, 1),
            "tech": round(tech * 100 if tech <= 1 else tech, 1),
            "hr": round(hr, 2),
            "reasons": reasons,
        },
    )


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
@login_required
def log_violation(request):
    """Increment violation counter for the current candidate and auto-lock if >3."""
    if request.method == "POST":
        try:
            profile = CandidateProfile.objects.get(user=request.user)
            profile.violations += 1
            profile.save()

            # auto reject if limit reached
            locked = False
            if profile.violations >= 3:
                profile.status = "rejected"
                profile.current_stage = "locked"
                profile.save()
                locked = True

            return JsonResponse({
                "status": "ok",
                "violations": profile.violations,
                "locked": locked
            })

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)
