import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env from backend/
load_dotenv(Path(__file__).parent / "backend" / ".env")

def check_readiness():
    print("CodeSentinel Readiness Audit\n" + "="*30)
    
    missing_vars = []
    required_vars = [
        "GITHUB_APP_ID", "GITHUB_APP_PRIVATE_KEY", 
        "DATABASE_URL", "REDIS_URL", "QDRANT_URL",
        "LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY"
    ]

    for var in required_vars:
        val = os.getenv(var)
        if not val:
            missing_vars.append(var)
            print(f"[MISSING] {var}")
        else:
            # Mask sensitive values
            masked = val[:4] + "*" * (len(val) - 4) if len(val) > 4 else "****"
            print(f"[SET] {var}: {masked}")

    print("\n" + "="*30)
    
    if missing_vars:
        print("\nAction Required: Please set the following in backend/.env:")
        for var in missing_vars:
            print(f"   - {var}")
        sys.exit(1)
    
    print("\nEverything looks ready for deployment!")
    print("Run: docker-compose up --build")

if __name__ == "__main__":
    check_readiness()
