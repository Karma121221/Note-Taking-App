import requests
import json
import os

# Test API endpoints
base_url = "https://note-taking-app-mu-six.vercel.app"

def test_root():
    print("Testing root endpoint...")
    response = requests.get(f"{base_url}/api/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_health():
    print("\nTesting health endpoint...")
    response = requests.get(f"{base_url}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_signup():
    print("\nTesting signup endpoint with fresh user...")
    import time
    timestamp = int(time.time())
    data = {
        "name": f"testuser{timestamp}",
        "email": f"test{timestamp}@example.com",
        "password": "123123",
        "role": "parent"
    }
    print(f"Sending signup data: {json.dumps(data, indent=2)}")
    response = requests.post(f"{base_url}/api/auth/signup", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return data["email"], data["password"]

def test_signin_with_credentials(email, password):
    print(f"\nTesting signin with {email}...")
    data = {
        "email": email,
        "password": password
    }
    print(f"Sending signin data: {json.dumps(data, indent=2)}")
    response = requests.post(f"{base_url}/api/auth/signin", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response

def test_simple_db_operation():
    print("\nTesting simple database operation...")
    # Test just a simple find_one operation
    import requests
    response = requests.get(f"{base_url}/api/folders/", headers={"Authorization": "Bearer test"})
    print(f"Simple DB operation status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_authenticated_endpoints():
    print("\nTesting authenticated endpoints flow...")

    # Step 1: Create a parent user and get their family code
    import requests
    import json

    parent_data = {
        "name": "testparent",
        "email": "parent@example.com",
        "password": "123123",
        "role": "parent"
    }

    print(f"Creating parent user: {parent_data['email']}")
    response = requests.post(f"{base_url}/api/auth/signup", json=parent_data)
    print(f"Parent signup status: {response.status_code}")

    if response.status_code == 200:
        parent_user = response.json()
        family_code = parent_user.get('family_code')
        print(f"Parent created with family code: {family_code}")

        # Step 2: Create a child user with the family code
        child_data = {
            "name": "testchild",
            "email": "child@example.com",
            "password": "123123",
            "role": "child",
            "family_code": family_code
        }

        print(f"Creating child user with family code: {family_code}")
        response = requests.post(f"{base_url}/api/auth/signup", json=child_data)
        print(f"Child signup status: {response.status_code}")

        if response.status_code == 200:
            child_user = response.json()
            print("Child user created successfully")

            # Step 3: Sign in as child to get token
            signin_data = {
                "email": "child@example.com",
                "password": "123123"
            }

            print("Signing in as child...")
            response = requests.post(f"{base_url}/api/auth/signin", json=signin_data)
            print(f"Child signin status: {response.status_code}")

            if response.status_code == 200:
                token_data = response.json()
                token = token_data.get('access_token')
                print(f"Got child token: {token[:20]}...")

                # Step 4: Test folders endpoint with child token
                print("Testing folders endpoint with child token...")
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(f"{base_url}/api/folders/", headers=headers)
                print(f"Folders endpoint status: {response.status_code}")
                print(f"Folders response: {response.json()}")

                # Step 5: Test creating a note as child
                print("Testing note creation as child...")
                note_data = {
                    "title": "Test Note",
                    "content": "This is a test note",
                    "folder_id": None
                }
                response = requests.post(f"{base_url}/api/notes/", json=note_data, headers=headers)
                print(f"Create note status: {response.status_code}")
                print(f"Create note response: {response.json()}")

            else:
                print(f"Child signin failed: {response.json()}")

        else:
            print(f"Child signup failed: {response.json()}")

    else:
        print(f"Parent signup failed: {response.json()}")

def test_serverless_function():
    print("\nTesting basic serverless function...")
    import requests
    try:
        # Test a simple POST without database
        response = requests.post(f"{base_url}/api/test-post",
                               json={"test": "serverless"},
                               timeout=10)
        print(f"Serverless function status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Serverless function test failed: {e}")

def test_signin():
    print("\nTesting signin endpoint...")
    data = {
        "email": "test@example.com",
        "password": "123123"
    }
    print(f"Sending signin data: {json.dumps(data, indent=2)}")
    response = requests.post(f"{base_url}/api/auth/signin", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

def test_mongo_connection():
    print("\nTesting direct MongoDB connection...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio

        # Get MongoDB URI from environment
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        print(f"Testing MongoDB connection with URI: {mongo_uri[:50]}...")

        # If no MONGO_URI in environment, use the production one from .env file
        if mongo_uri == "mongodb://localhost:27017":
            mongo_uri = "mongodb+srv://namit_thing:heyyup@cluster0.xgtzgla.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            print(f"Using production MongoDB URI: {mongo_uri[:50]}...")

        # Create client with same settings as production
        client = AsyncIOMotorClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=45000,
            maxPoolSize=1,
            minPoolSize=0,
            maxIdleTimeMS=30000,
            retryWrites=True,
            retryReads=True,
        )

        async def test_connection():
            try:
                # Test ping
                print("Sending ping to MongoDB...")
                ping_result = await client.admin.command('ping')
                print(f"MongoDB ping successful: {ping_result}")

                # Test database access
                db = client["note_taking_app"]
                print("Database access successful")

                # Test collection access
                collection = db["users"]
                print("Collection access successful")

                # Test a simple find operation
                count = await collection.count_documents({})
                print(f"Document count in users collection: {count}")

                return True
            except Exception as e:
                print(f"MongoDB connection test failed: {e}")
                import traceback
                print(f"Full traceback: {traceback.format_exc()}")
                return False
            finally:
                client.close()

        # Run the async test
        result = asyncio.run(test_connection())
        print(f"Connection test result: {result}")

    except Exception as e:
        print(f"Failed to create MongoDB client: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_root()
    test_health()
    test_serverless_function()
    email, password = test_signup()
    test_signin_with_credentials(email, password)
    test_mongo_connection()
    test_simple_db_operation()
    test_authenticated_endpoints()