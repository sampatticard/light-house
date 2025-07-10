#!/usr/bin/env python3
"""
Test script to verify browser automation setup
"""
import asyncio
import sys
import os
from browser_toolkit import BrowserUseToolkit

async def test_browser_setup():
    """Test basic browser functionality"""
    print("🧪 Testing Browser Setup")
    print("=" * 30)
    
    try:
        # Initialize browser toolkit
        print("1. Initializing browser toolkit...")
        toolkit = BrowserUseToolkit()
        
        # Test page state
        print("2. Getting page state...")
        state = await toolkit.get_page_state()
        print(f"   Page state: {state[:100]}...")
        
        # Test simple navigation
        print("3. Testing navigation...")
        # Use a valid agent prompt, not a navigation command
        navigation_task = "Go to https://www.google.com and wait for the page to load."
        result = await toolkit.execute_browser_task(navigation_task)
        print(f"   Navigation result: {type(result)}")
        
        # Get updated state
        print("4. Getting updated page state...")
        new_state = await toolkit.get_page_state()
        print(f"   Updated state: {new_state[:100]}...")
        
        print("\n✅ Browser setup test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Browser setup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_ayushman_navigation():
    """Test navigation to Ayushman portal"""
    print("\n🏥 Testing Ayushman Portal Navigation")
    print("=" * 40)
    
    try:
        toolkit = BrowserUseToolkit()
        
        print("1. Navigating to Ayushman portal...")
        # Use a valid agent prompt
        ayushman_task = "Go to https://beneficiary.nha.gov.in/ and wait for the page to load."
        result = await toolkit.execute_browser_task(ayushman_task)
        
        print("2. Getting page state...")
        state = await toolkit.get_page_state()
        print(f"   Portal state: {state[:200]}...")
        
        if "beneficiary.nha.gov.in" in state:
            print("✅ Successfully navigated to Ayushman portal!")
            return True
        else:
            print("⚠️  Navigation completed but URL verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Ayushman navigation test failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Browser Automation Test Suite")
    print("=" * 50)
    
    # Test 1: Basic browser setup
    basic_test = await test_browser_setup()
    
    if basic_test:
        # Test 2: Ayushman portal navigation
        ayushman_test = await test_ayushman_navigation()
        
        if ayushman_test:
            print("\n🎉 All tests passed! Your setup is ready.")
        else:
            print("\n⚠️  Basic setup works, but Ayushman navigation needs attention.")
    else:
        print("\n❌ Basic setup failed. Please check Chrome and dependencies.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())