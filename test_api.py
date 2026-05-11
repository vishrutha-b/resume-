import traceback
from ats_evaluator import ATSEvaluator
from dotenv import load_dotenv

load_dotenv()

try:
    print("Initializing Evaluator...")
    evaluator = ATSEvaluator()
    print("Testing Evaluate...")
    res = evaluator.evaluate("Python developer", "Senior Python Role")
    print(res.model_dump_json(indent=2))
except Exception as e:
    print("ERROR CAUGHT:")
    traceback.print_exc()
