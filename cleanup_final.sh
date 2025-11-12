#!/bin/bash

# Final cleanup - Keep only essentials for API

echo "Cleaning up unnecessary files..."

# Delete all markdown files
/usr/bin/rm -f CHEATSHEET.md
/usr/bin/rm -f DEPLOYMENT.md
/usr/bin/rm -f EXAMPLES.md
/usr/bin/rm -f FILES.md
/usr/bin/rm -f MEVO_SETUP.md
/usr/bin/rm -f PROJECT_SUMMARY.md
/usr/bin/rm -f QUICKSTART.md
/usr/bin/rm -f README_GO.md
/usr/bin/rm -f TEST_QUICK_REFERENCE.md
/usr/bin/rm -f TESTING.md

# Delete Go files
/usr/bin/rm -f main.go
/usr/bin/rm -f main_test.go
/usr/bin/rm -f providers.go
/usr/bin/rm -f providers_test.go
/usr/bin/rm -f integration_test.go
/usr/bin/rm -f go.mod

# Delete test files
/usr/bin/rm -f test_app.py
/usr/bin/rm -f test_providers.py
/usr/bin/rm -f test_integration.py
/usr/bin/rm -f test_data.json

# Delete scripts
/usr/bin/rm -f test_api.sh
/usr/bin/rm -f setup.sh
/usr/bin/rm -f Makefile

# Delete this cleanup script itself
/usr/bin/rm -f cleanup.sh

echo "Cleanup complete!"
echo ""
echo "Remaining files (API essentials only):"
/usr/bin/ls -lah | grep -v "^d" | grep -v "^total"
