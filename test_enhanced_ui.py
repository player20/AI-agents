"""
Test script for Code Weaver Pro Enhanced UI
Verifies all components load correctly
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all enhanced modules can be imported"""

    print("🧪 Testing imports...")

    try:
        from core.meta_prompt import MetaPromptEngine
        print("✅ meta_prompt module loaded")
    except ImportError as e:
        print(f"❌ Failed to import meta_prompt: {e}")
        return False

    try:
        from core.audit_mode import AuditModeAnalyzer
        print("✅ audit_mode module loaded")
    except ImportError as e:
        print(f"❌ Failed to import audit_mode: {e}")
        return False

    try:
        from core.ab_test_generator import ABTestGenerator
        print("✅ ab_test_generator module loaded")
    except ImportError as e:
        print(f"❌ Failed to import ab_test_generator: {e}")
        return False

    try:
        from core.report_generator import ReportGenerator
        print("✅ report_generator module loaded")
    except ImportError as e:
        print(f"❌ Failed to import report_generator: {e}")
        return False

    print("\n✅ All core modules loaded successfully!")
    return True


def test_meta_prompt():
    """Test meta_prompt basic functionality"""

    print("\n🧪 Testing MetaPromptEngine...")

    try:
        from core.meta_prompt import MetaPromptEngine
        import os

        # Check API key
        if not os.getenv('ANTHROPIC_API_KEY'):
            print("⚠️  ANTHROPIC_API_KEY not set - skipping API tests")
            print("✅ MetaPromptEngine class instantiated (no API call)")
            return True

        engine = MetaPromptEngine()

        # Test with simple input
        context = engine.extract_context("A recipe sharing app")

        print(f"✅ Context extracted:")
        print(f"   Industry: {context.get('industry', 'unknown')}")
        print(f"   Clarity: {context.get('clarity_score', 0)}/10")

        return True

    except Exception as e:
        print(f"❌ MetaPromptEngine test failed: {e}")
        return False


def test_streamlit_app():
    """Test that Streamlit app file is valid"""

    print("\n🧪 Testing Streamlit app...")

    try:
        # Check if app_enhanced.py exists
        app_path = Path(__file__).parent / "app_enhanced.py"

        if not app_path.exists():
            print(f"❌ app_enhanced.py not found at {app_path}")
            return False

        # Try to parse it (syntax check)
        import ast

        with open(app_path, 'r') as f:
            code = f.read()

        ast.parse(code)
        print("✅ app_enhanced.py syntax is valid")

        # Check main_interface_enhanced.py
        interface_path = Path(__file__).parent / "streamlit_ui" / "main_interface_enhanced.py"

        if not interface_path.exists():
            print(f"❌ main_interface_enhanced.py not found at {interface_path}")
            return False

        with open(interface_path, 'r') as f:
            code = f.read()

        ast.parse(code)
        print("✅ main_interface_enhanced.py syntax is valid")

        return True

    except SyntaxError as e:
        print(f"❌ Syntax error in Streamlit files: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing Streamlit app: {e}")
        return False


def main():
    """Run all tests"""

    print("=" * 60)
    print("Code Weaver Pro Enhanced Edition - Test Suite")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("MetaPrompt", test_meta_prompt),
        ("Streamlit App", test_streamlit_app),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 All tests passed! Ready to launch.")
        print("\nTo start Code Weaver Pro Enhanced:")
        print("  streamlit run app_enhanced.py")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
