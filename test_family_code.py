#!/usr/bin/env python3
"""
Test script to verify family code functionality
Run this to test the complete family code flow
"""
import asyncio
import httpx
import json
import sys

BASE_URL = "https://note-taking-app-mu-six.vercel.app/api"

async def test_family_code_flow():
    """Test the complete family code flow"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("🧪 Testing Family Code Flow")
        print("=" * 50)

        # Test 1: Create Parent Account
        print("\n1️⃣ Creating Parent Account...")
        import time
        timestamp = int(time.time())
        parent_data = {
            "name": "Test Parent",
            "email": f"testparent{timestamp}@example.com",
            "password": "testpass123",
            "role": "parent"
        }

        try:
            response = await client.post(f"{BASE_URL}/auth/signup", json=parent_data)
            if response.status_code == 200:
                parent = response.json()
                print(f"✅ Parent created: {parent.get('name')} ({parent.get('email')})")
                print(f"📧 Parent ID: {parent.get('id')}")
            else:
                print(f"❌ Failed to create parent: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating parent: {e}")
            return False

        # Test 2: Get Parent Info (should include family_code)
        print("\n2️⃣ Getting Parent Info...")
        try:
            # First need to login to get token
            login_response = await client.post(f"{BASE_URL}/auth/signin", json={
                "email": parent_data["email"],
                "password": parent_data["password"]
            })

            if login_response.status_code == 200:
                token_data = login_response.json()
                token = token_data["access_token"]

                # Get parent info with auth header
                headers = {"Authorization": f"Bearer {token}"}
                user_response = await client.get(f"{BASE_URL}/auth/me", headers=headers)

                if user_response.status_code == 200:
                    user_data = user_response.json()
                    print(f"✅ Parent info retrieved: {user_data.get('name')}")
                    print(f"🔑 Family Code: {user_data.get('family_code')}")
                    print(f"👶 Children IDs: {user_data.get('children_ids', [])}")
                else:
                    print(f"❌ Failed to get parent info: {user_response.text}")
                    return False
            else:
                print(f"❌ Failed to login: {login_response.text}")
                return False
        except Exception as e:
            print(f"❌ Error getting parent info: {e}")
            return False

        # Test 3: Create Child Account
        print("\n3️⃣ Creating Child Account...")
        child_data = {
            "name": "Test Child",
            "email": f"testchild{timestamp}@example.com",
            "password": "testpass123",
            "role": "child"
        }

        try:
            response = await client.post(f"{BASE_URL}/auth/signup", json=child_data)
            if response.status_code == 200:
                child = response.json()
                print(f"✅ Child created: {child.get('name')} ({child.get('email')})")
                print(f"📧 Child ID: {child.get('id')}")
            else:
                print(f"❌ Failed to create child: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error creating child: {e}")
            return False

        # Test 4: Child Login and Try to Join Family
        print("\n4️⃣ Child Login and Join Family...")
        try:
            # Child login
            login_response = await client.post(f"{BASE_URL}/auth/signin", json={
                "email": child_data["email"],
                "password": child_data["password"]
            })

            if login_response.status_code == 200:
                child_token_data = login_response.json()
                child_token = child_token_data["access_token"]

                # Get child user info
                headers = {"Authorization": f"Bearer {child_token}"}
                child_user_response = await client.get(f"{BASE_URL}/auth/me", headers=headers)

                if child_user_response.status_code == 200:
                    child_user = child_user_response.json()
                    print(f"✅ Child logged in: {child_user.get('name')}")
                    print(f"👨‍👩‍👧‍👦 Parent ID (should be null): {child_user.get('parent_id')}")

                    # Try to join family with family code
                    # We need the family code from step 2
                    family_code = user_data.get('family_code')
                    if family_code:
                        join_response = await client.post(f"{BASE_URL}/family/join-family",
                            json={"family_code": family_code},
                            headers=headers)

                        if join_response.status_code == 200:
                            print(f"✅ Child successfully joined family!")
                            print(f"📝 Response: {join_response.json()}")
                        else:
                            print(f"❌ Failed to join family: {join_response.text}")
                            return False
                    else:
                        print("❌ No family code available from parent")
                        return False
                else:
                    print(f"❌ Failed to get child info: {child_user_response.text}")
                    return False
            else:
                print(f"❌ Failed to login child: {login_response.text}")
                return False
        except Exception as e:
            print(f"❌ Error in child login/join: {e}")
            return False

        # Test 5: Verify Parent-Child Connection
        print("\n5️⃣ Verifying Parent-Child Connection...")
        try:
            # Check parent's children list
            parent_headers = {"Authorization": f"Bearer {token}"}
            parent_response = await client.get(f"{BASE_URL}/auth/me", headers=parent_headers)

            if parent_response.status_code == 200:
                updated_parent = parent_response.json()
                print(f"✅ Parent now has {len(updated_parent.get('children_ids', []))} children")
                if updated_parent.get('children_ids'):
                    print(f"👶 Children IDs: {updated_parent.get('children_ids')}")
                else:
                    print("❌ Parent has no children (connection failed)")
                    return False
            else:
                print(f"❌ Failed to get updated parent info: {parent_response.text}")
                return False
        except Exception as e:
            print(f"❌ Error verifying connection: {e}")
            return False

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED! Family code flow is working correctly.")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_family_code_flow())
    if not success:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
    else:
        print("\n✅ Family code functionality is working correctly!")