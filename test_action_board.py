"""
Test Action Board Functionality

This script tests the action synthesizer and code generators
using the actual agent output from your evaluation.
"""

import json
from pathlib import Path
from action_synthesizer import ActionSynthesizer, generate_project_plan_from_outputs
from code_generators import CodeGenerator


def test_action_synthesis():
    """Test action synthesizer with real agent outputs"""

    print("[TEST] Testing Action Synthesizer...\n")

    # Find latest export
    exports_dir = Path("exports")
    json_exports = list(exports_dir.glob("*.json"))

    if not json_exports:
        print("[X] No exports found. Run the platform first!")
        return False

    latest_export = max(json_exports, key=lambda p: p.stat().st_mtime)
    print(f"[FILE] Using export: {latest_export.name}\n")

    # Load export
    with open(latest_export, 'r') as f:
        data = json.load(f)

    agent_outputs = data['agent_outputs']

    # Test synthesis
    synthesizer = ActionSynthesizer()
    actions = synthesizer.synthesize(agent_outputs)

    print("[OK] Action Synthesis Results:\n")
    print(f"   Quick Wins: {len(actions['quick_wins'])}")
    print(f"   Short-term: {len(actions['short_term'])}")
    print(f"   Medium-term: {len(actions['medium_term'])}")
    print(f"   Long-term: {len(actions['long_term'])}")
    print(f"   Code Gen Opportunities: {len(actions['code_generation_opportunities'])}\n")

    # Show quick wins
    if actions['quick_wins']:
        print("[LIST] Quick Wins (Week 1-2):")
        for action in actions['quick_wins']:
            can_gen = "[BOT]" if action.get('can_generate_code') else "     "
            print(f"   {can_gen} • {action['title']}")
        print("")

    # Show code gen opportunities
    if actions['code_generation_opportunities']:
        print("[BOT] Code Generation Available:")
        for opp in actions['code_generation_opportunities']:
            print(f"   • {opp['action']} -> {opp['generator']}()")
        print("")

    return True


def test_project_plan_generation():
    """Test PROJECT_PLAN.md generation"""

    print("[TEST] Testing Project Plan Generation...\n")

    # Find latest export
    exports_dir = Path("exports")
    json_exports = list(exports_dir.glob("*.json"))

    if not json_exports:
        print("[X] No exports found")
        return False

    latest_export = max(json_exports, key=lambda p: p.stat().st_mtime)

    # Load export
    with open(latest_export, 'r') as f:
        data = json.load(f)

    project_name = data['metadata'].get('project_name', 'Test Project')
    agent_outputs = data['agent_outputs']

    # Generate plan
    plan = generate_project_plan_from_outputs(agent_outputs, project_name)

    # Show preview
    lines = plan.split('\n')
    print("[FILE] PROJECT_PLAN.md Preview (first 30 lines):\n")
    print("-" * 60)
    for line in lines[:30]:
        # Handle unicode characters for Windows console - replace emojis with ?
        safe_line = line.encode('ascii', 'replace').decode('ascii')
        print(safe_line)
    print("-" * 60)
    print(f"\nTotal lines: {len(lines)}")
    print("")

    return True


def test_code_generators():
    """Test code generation functions"""

    print("[TEST] Testing Code Generators...\n")

    generator = CodeGenerator()

    # Test CLI generation
    print("[CLI] CLI Generator:")
    cli_files = generator.generate_cli_starter()
    print(f"   [OK] Generated {len(cli_files)} files:")
    for filename in cli_files.keys():
        print(f"      • {filename}")
    print("")

    # Test Docker generation
    print("[DOCKER] Docker Generator:")
    docker_files = generator.generate_docker_files()
    print(f"   [OK] Generated {len(docker_files)} files:")
    for filename in docker_files.keys():
        print(f"      • {filename}")
    print("")

    # Test Templates generation
    print("[TEMPLATES] Templates Generator:")
    template_files = generator.generate_workflow_templates()
    print(f"   [OK] Generated {len(template_files)} templates:")
    for filename in list(template_files.keys())[:5]:  # Show first 5
        print(f"      • {filename}")
    print(f"      ... and {len(template_files) - 5} more")
    print("")

    # Test API generation
    print("[API] API Generator:")
    api_files = generator.generate_api_starter()
    print(f"   [OK] Generated {len(api_files)} files:")
    for filename in api_files.keys():
        print(f"      • {filename}")
    print("")

    # Test Community files generation
    print("[COMMUNITY] Community Files Generator:")
    community_files = generator.generate_community_files()
    print(f"   [OK] Generated {len(community_files)} files:")
    for filename in community_files.keys():
        print(f"      • {filename}")
    print("")

    return True


def main():
    """Run all tests"""

    print("=" * 60)
    print("  ACTION BOARD TEST SUITE")
    print("=" * 60)
    print("")

    # Test 1: Action Synthesis
    test_1_passed = test_action_synthesis()

    # Test 2: Project Plan Generation
    test_2_passed = test_project_plan_generation()

    # Test 3: Code Generators
    test_3_passed = test_code_generators()

    # Summary
    print("=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    print(f"Action Synthesis:       {'[OK] PASS' if test_1_passed else '[X] FAIL'}")
    print(f"Project Plan:           {'[OK] PASS' if test_2_passed else '[X] FAIL'}")
    print(f"Code Generators:        {'[OK] PASS' if test_3_passed else '[X] FAIL'}")
    print("")

    if all([test_1_passed, test_2_passed, test_3_passed]):
        print("[SUCCESS] All tests passed!")
        print("")
        print("Next steps:")
        print("  1. Run: python generate_essentials.py --all")
        print("  2. Read: ACTION_BOARD_README.md")
        print("  3. Build: Follow your PROJECT_PLAN.md")
    else:
        print("[X] Some tests failed. Check the output above.")

    print("")


if __name__ == "__main__":
    main()
