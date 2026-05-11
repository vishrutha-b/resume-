import os
import json
from app import app
from models.schemas import ATSResponseSchema
from ats_evaluator import ATSEvaluator

dummy_json = {
  "ats_score": 88,
  "verifiability_score": 65,
  "skill_match": {
    "matched": ["React", "Python", "Flask", "AWS"],
    "missing": ["Kubernetes", "GraphQL"],
    "partial": ["Postgres"],
    "implicit": ["EC2", "S3", "RDS"],
    "stale": ["jQuery", "PHP"]
  },
  "bs_flags": ["Claimed to 'single-handedly scale systems to 50M users' but only lists 1 year of junior experience."],
  "interview_questions": [
    "You mentioned scaling to 50M users. What specific load balancing strategies did you configure?",
    "Since it has been >3 years since you used PHP, how would you approach maintaining our legacy PHP monolith today?",
    "You implicitly demonstrate AWS knowledge via EC2. Walk me through a secure VPC architecture."
  ],
  "domain_fit": "High",
  "experience_fit": "Medium",
  "key_gaps": ["Lacks modern container orchestration (K8s)."],
  "strong_points": ["Excellent core AWS understanding.", "Strong frontend React capabilities."],
  "recommendations": ["Proceed to technical interview focusing on the BS flags to verify actual impact."]
}

# Override to bypass API for reliable UI testing
def mocked_evaluate(self, resume_text, job_desc):
    print("MOCKED EVALUATE TRIGGERED FOR UI TEST")
    return ATSResponseSchema(**dummy_json)

ATSEvaluator.evaluate = mocked_evaluate

if __name__ == '__main__':
    print("Starting test server on port 5005...")
    app.run(host='127.0.0.1', port=5005, debug=False)
