"""
Tests for the Mergington High School Activities API

Uses the AAA (Arrange-Act-Assert) pattern for clear test structure
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app
import copy


@pytest.fixture
def client():
    """Fixture that provides a test client with fresh activities data"""
    # Arrange: Create a fresh copy of the activities for each test
    from src import app as app_module
    
    # Store the original activities
    original_activities = copy.deepcopy(app_module.activities)
    
    # Create test client
    test_client = TestClient(app)
    
    yield test_client
    
    # Reset activities after each test to ensure isolation
    app_module.activities.clear()
    app_module.activities.update(original_activities)


class TestRootEndpoint:
    """Tests for GET / endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """
        Arrange: GET request to root endpoint
        Act: Send request with follow_redirects disabled
        Assert: Should return 307 redirect to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint"""
    
    def test_get_all_activities(self, client):
        """
        Arrange: No setup needed - activities already populated
        Act: Send GET request to /activities
        Assert: Should return all activities with correct structure
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) > 0
        assert "Chess Club" in activities
        assert "Programming Class" in activities
    
    def test_activity_structure(self, client):
        """
        Arrange: No setup needed
        Act: Get activities and check structure of one activity
        Assert: Each activity should have required fields
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        # Assert
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """
        Arrange: Prepare valid activity name and email
        Act: Sign up a new student for an activity
        Assert: Should return success and participant should be added
        """
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}",
            follow_redirects=False
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert email in result["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self, client):
        """
        Arrange: Use non-existent activity name
        Act: Try to sign up for non-existent activity
        Assert: Should return 404 error
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        result = response.json()
        assert result["detail"] == "Activity not found"
    
    def test_signup_duplicate_participant(self, client):
        """
        Arrange: Student already signed up for an activity
        Act: Try to sign up the same student again
        Assert: Should return 400 error for duplicate signup
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]
    
    def test_signup_different_activities(self, client):
        """
        Arrange: New student for multiple different activities
        Act: Sign up the same student for two different activities
        Assert: Should succeed for both activities
        """
        # Arrange
        email = "multiactivity@mergington.edu"
        activities_list = ["Chess Club", "Programming Class"]
        
        # Act & Assert - First signup
        response1 = client.post(
            f"/activities/{activities_list[0]}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Act & Assert - Second signup
        response2 = client.post(
            f"/activities/{activities_list[1]}/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify in both activities
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activities_list[0]]["participants"]
        assert email in activities[activities_list[1]]["participants"]


class TestUnregisterEndpoint:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client):
        """
        Arrange: Student is already registered for an activity
        Act: Unregister the student
        Assert: Should return success and participant should be removed
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """
        Arrange: Use non-existent activity name
        Act: Try to unregister from non-existent activity
        Assert: Should return 404 error
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        result = response.json()
        assert result["detail"] == "Activity not found"
    
    def test_unregister_not_signed_up(self, client):
        """
        Arrange: Student is not registered for the activity
        Act: Try to unregister a student who isn't signed up
        Assert: Should return 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "not signed up" in result["detail"]
    
    def test_unregister_twice(self, client):
        """
        Arrange: Unregister a student once successfully
        Act: Try to unregister the same student again
        Assert: Second unregister should fail with 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act - First unregister
        response1 = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert response1.status_code == 200
        
        # Act - Second unregister
        response2 = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        
        # Assert
        assert response2.status_code == 400
        result = response2.json()
        assert "not signed up" in result["detail"]
    
    def test_signup_and_unregister_cycle(self, client):
        """
        Arrange: Add a new participant and then remove them
        Act: Sign up then unregister
        Assert: Participant count should return to original
        """
        # Arrange
        activity_name = "Chess Club"
        email = "cycle@mergington.edu"
        
        # Get original count
        original_response = client.get("/activities")
        original_activities = original_response.json()
        original_count = len(original_activities[activity_name]["participants"])
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Assert - Participant added
        after_signup = client.get("/activities")
        after_signup_activities = after_signup.json()
        assert len(after_signup_activities[activity_name]["participants"]) == original_count + 1
        
        # Act - Unregister
        unregister_response = client.post(
            f"/activities/{activity_name}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Assert - Back to original count
        final_response = client.get("/activities")
        final_activities = final_response.json()
        assert len(final_activities[activity_name]["participants"]) == original_count
