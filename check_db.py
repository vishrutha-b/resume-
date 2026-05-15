import json
from models.database import get_db

db = get_db()
evals = list(db.evaluations.find().sort("updated_at", -1).limit(5))

for e in evals:
    print("-------------------------")
    print(f"ID: {e['_id']}")
    print(f"ATS Score: {e.get('ats_score')}")
    print(f"Filename: {e.get('candidate_filename')}")
    
    # Let's see the optimized resume's score if it exists
    opt_data_raw = e.get("optimized_resume_data")
    if opt_data_raw:
        try:
            opt_data = json.loads(opt_data_raw)
            print(f"Optimized ATS Score Estimate (Backend final score): {opt_data.get('ats_score_estimate')}")
            # Also print the breakdown from the original evaluation (which was updated with the optimized score)
            print(f"Breakdown: {e.get('raw_json_data')}")
        except:
            print("Could not parse opt data")
    else:
        print("No optimization data")
