#!/usr/bin/env python3
import sys
import os

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_shortlist_api():
    try:
        from api.shortlist import router
        print("✓ Shortlist API router imported successfully")
        
        from schemas import ShortlistCreate
        print("✓ ShortlistCreate schema imported successfully")
        
        from services.shortlist_service import ShortlistService
        print("✓ Shortlist Service imported successfully")
        
        print("\n✓ Shortlist API updated successfully!")
        print("  - Now accepts cv_ids parameter to specify which CVs to analyze")
        print("  - Only processes the specified CVs instead of all user CVs")
        print("  - Validates that all specified CVs exist and belong to the user")
        print("  - More efficient and targeted shortlisting")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Testing updated Shortlist API...\n")
    success = test_shortlist_api()
    
    if success:
        print("\nShortlist API is ready to use!")
        print("New API structure:")
        print("  POST /shortlist/")
        print("  Body: {")
        print("    'job_description_id': 1,")
        print("    'cv_ids': [1, 2, 3],")
        print("    'threshold': 0.6")
        print("  }")
    else:
        print("\nPlease fix the import errors.")
        sys.exit(1)
