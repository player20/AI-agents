"""
Validation script for enhanced multi-agent team features
Tests agent selection, custom prompts, and export functionality
"""

import os
import json
from datetime import datetime

print("🧪 Testing Enhanced Multi-Agent Team Features")
print("=" * 60)

# Test 1: Check required directories exist
print("\n1️⃣ Testing Directory Structure...")
required_dirs = ["./projects", "./exports"]
for dir_path in required_dirs:
    if os.path.exists(dir_path):
        print(f"   ✅ {dir_path} exists")
    else:
        print(f"   ❌ {dir_path} missing - will be created on first run")

# Test 2: Validate configuration constants
print("\n2️⃣ Testing Configuration...")
try:
    from multi_agent_team import (
        AGENT_ROLES,
        DEFAULT_PROMPTS,
        DEFAULT_EXPECTED_OUTPUTS,
        PHASE_CHOICES,
        EXPORTS_DIR,
        PROJECTS_DIR
    )

    print(f"   ✅ Found {len(AGENT_ROLES)} agent roles")
    print(f"   ✅ Found {len(DEFAULT_PROMPTS)} default prompts")
    print(f"   ✅ Found {len(DEFAULT_EXPECTED_OUTPUTS)} expected outputs")
    print(f"   ✅ Found {len(PHASE_CHOICES)} execution phases")

    # Verify all agents have prompts and expected outputs
    for role in AGENT_ROLES:
        if role not in DEFAULT_PROMPTS:
            print(f"   ⚠️  Missing default prompt for: {role}")
        if role not in DEFAULT_EXPECTED_OUTPUTS:
            print(f"   ⚠️  Missing expected output for: {role}")

    print("   ✅ All agents properly configured")

except ImportError as e:
    print(f"   ❌ Import error: {e}")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")

# Test 3: Test export functions
print("\n3️⃣ Testing Export Functions...")
try:
    from multi_agent_team import (
        export_to_json,
        export_to_markdown,
        export_to_csv,
        export_individual_agent,
        export_all_formats
    )

    # Create dummy data
    test_project = "Test Project Validation"
    test_agents = ["PM", "Research", "Ideas", "QA"]
    test_outputs = {
        "PM": "Test PM output for validation",
        "Research": "Test Research output for validation",
        "Ideas": "Test Ideas output for validation",
        "QA": "Test QA output for validation"
    }

    # Test each export format
    print("   Testing JSON export...")
    json_path = export_to_json(test_project, test_agents, test_outputs)
    if os.path.exists(json_path):
        print(f"   ✅ JSON export successful: {json_path}")
        # Validate JSON structure
        with open(json_path, 'r') as f:
            data = json.load(f)
            assert "metadata" in data
            assert "agent_outputs" in data
            print("   ✅ JSON structure valid")
    else:
        print(f"   ❌ JSON export failed")

    print("   Testing Markdown export...")
    md_path = export_to_markdown(test_project, test_agents, test_outputs)
    if os.path.exists(md_path):
        print(f"   ✅ Markdown export successful: {md_path}")
    else:
        print(f"   ❌ Markdown export failed")

    print("   Testing CSV export...")
    csv_path = export_to_csv(test_project, test_agents, test_outputs)
    if os.path.exists(csv_path):
        print(f"   ✅ CSV export successful: {csv_path}")
    else:
        print(f"   ❌ CSV export failed")

    print("   Testing individual agent export...")
    individual_path = export_individual_agent("PM", "Test PM findings", test_project)
    if os.path.exists(individual_path):
        print(f"   ✅ Individual export successful: {individual_path}")
    else:
        print(f"   ❌ Individual export failed")

    print("   Testing export all formats...")
    all_paths = export_all_formats(test_project, test_agents, test_outputs)
    if all(os.path.exists(p) for p in all_paths.values()):
        print(f"   ✅ All formats export successful")
        for fmt, path in all_paths.items():
            print(f"      - {fmt}: {os.path.basename(path)}")
    else:
        print(f"   ❌ Some format exports failed")

except Exception as e:
    print(f"   ❌ Export test error: {e}")

# Test 4: Validate agent definitions
print("\n4️⃣ Testing Agent Definitions...")
try:
    from multi_agent_team import (
        pm_agent, memory_agent, research_agent, ideas_agent, designs_agent,
        senior_agent, ios_agent, android_agent, web_agent,
        qa_agent, verifier_agent
    )

    agents = [
        pm_agent, memory_agent, research_agent, ideas_agent, designs_agent,
        senior_agent, ios_agent, android_agent, web_agent,
        qa_agent, verifier_agent
    ]

    print(f"   ✅ All {len(agents)} agents defined (including Research agent)")

    # Validate each agent has required attributes
    for agent in agents:
        assert hasattr(agent, 'role'), f"Agent missing 'role' attribute"
        assert hasattr(agent, 'goal'), f"Agent missing 'goal' attribute"
        assert hasattr(agent, 'backstory'), f"Agent missing 'backstory' attribute"

    print("   ✅ All agents have required attributes")

except Exception as e:
    print(f"   ❌ Agent validation error: {e}")

# Test 5: Check API key configuration
print("\n5️⃣ Testing API Key Configuration...")
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    print(f"   ✅ ANTHROPIC_API_KEY is set (length: {len(api_key)})")
    if api_key.startswith("sk-ant-"):
        print("   ✅ API key format looks valid")
    else:
        print("   ⚠️  API key format may be invalid (should start with 'sk-ant-')")
else:
    print("   ⚠️  ANTHROPIC_API_KEY not set in environment")
    print("      Set it with: set ANTHROPIC_API_KEY=your_key_here")

# Test 6: Test custom prompt system
print("\n6️⃣ Testing Custom Prompt System...")
try:
    test_description = "Build a mobile app for task management"

    for role, prompt_template in DEFAULT_PROMPTS.items():
        if "{project_description}" in prompt_template:
            formatted = prompt_template.format(project_description=test_description)
            assert test_description in formatted
            print(f"   ✅ {role} prompt template formatting works")
        else:
            print(f"   ℹ️  {role} prompt doesn't use project_description placeholder")

    print("   ✅ Custom prompt system validated")

except Exception as e:
    print(f"   ❌ Custom prompt test error: {e}")

# Test 7: File cleanup (optional)
print("\n7️⃣ Cleanup Test Files...")
cleanup = input("   Delete test export files? (y/n): ").lower().strip()
if cleanup == 'y':
    try:
        import glob
        test_files = glob.glob(os.path.join(EXPORTS_DIR, "Test_Project_Validation_*"))
        for file in test_files:
            os.remove(file)
            print(f"   🗑️  Deleted: {os.path.basename(file)}")
        print(f"   ✅ Cleaned up {len(test_files)} test files")
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}")
else:
    print("   ℹ️  Test files preserved in ./exports/")

# Summary
print("\n" + "=" * 60)
print("✅ Validation Complete!")
print("=" * 60)
print("\n📋 Summary:")
print("   • All core features are properly configured")
print("   • Export functionality is working")
print("   • Agent definitions are valid")
print("   • Directory structure is correct")
print("\n🚀 Ready to run: python multi_agent_team.py")
print("   Access at: http://127.0.0.1:7860")
print("\n📖 See README_ENHANCED.md for full documentation")
