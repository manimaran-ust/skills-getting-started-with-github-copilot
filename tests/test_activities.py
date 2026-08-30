"""
FastAPI backend tests using the AAA (Arrange-Act-Assert) pattern.
Tests cover all endpoints: GET /activities, POST /signup, POST /unregister.
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: No setup needed for redirect test
        Act: Make GET request to root
        Assert: Verify redirect status and location
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_all_activities_returns_success(self, client, reset_activities):
        """
        Arrange: Activities fixture sets up initial data
        Act: Make GET request to /activities
        Assert: Verify all activities are returned with correct structure
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        assert response.status_code == 200
        assert len(activities) == 3
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
    
    def test_activity_contains_required_fields(self, client, reset_activities):
        """
        Arrange: Activities fixture provides data
        Act: Fetch activities and inspect structure
        Assert: Verify each activity has required fields
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
    
    def test_participants_list_is_correct(self, client, reset_activities):
        """
        Arrange: Activities fixture with known participants
        Act: Fetch activities
        Assert: Verify participant lists match expected values
        """
        # Act
        response = client.get("/activities")
        activities = response.json()
        chess_participants = activities["Chess Club"]["participants"]
        
        # Assert
        assert len(chess_participants) == 2
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_successful_signup(self, client, reset_activities):
        """
        Arrange: New student email and available activity
        Act: Make POST request to signup endpoint
        Assert: Verify success message and response status
        """
        # Arrange
        activity_name = "Gym Class"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """
        Arrange: Get initial participant count
        Act: Sign up a new student
        Assert: Verify participant was added to the activity
        """
        # Arrange
        activity_name = "Gym Class"
        email = "newstudent@mergington.edu"
        
        # Act
        client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        participants = activities[activity_name]["participants"]
        assert email in participants
        assert len(participants) == 3  # Was 2, now 3
    
    def test_duplicate_signup_returns_error(self, client, reset_activities):
        """
        Arrange: Student already signed up for an activity
        Act: Try to sign up the same student again
        Assert: Verify 400 error with appropriate message
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_to_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Activity that doesn't exist
        Act: Try to sign up for non-existent activity
        Assert: Verify 404 error
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_to_full_activity_returns_error(self, client, reset_activities):
        """
        Arrange: Fill an activity to capacity, try to add one more
        Act: Sign up students until capacity reached, then one more
        Assert: Verify capacity error on final signup
        """
        # Arrange
        from src.app import activities
        activity_name = "Programming Class"
        activities[activity_name]["max_participants"] = 2  # Set low capacity
        activities[activity_name]["participants"] = ["student1@mergington.edu", "student2@mergington.edu"]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow@mergington.edu"}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestUnregisterEndpoint:
    """Tests for the POST /activities/{activity_name}/unregister endpoint."""
    
    def test_successful_unregister(self, client, reset_activities):
        """
        Arrange: Student currently signed up for an activity
        Act: Make POST request to unregister
        Assert: Verify success message and response status
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """
        Arrange: Verify student is in participant list
        Act: Unregister the student
        Assert: Verify student no longer in participant list
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # Act
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        participants = activities[activity_name]["participants"]
        assert email not in participants
        assert len(participants) == initial_count - 1
    
    def test_unregister_nonexistent_student_returns_error(self, client, reset_activities):
        """
        Arrange: Student not signed up for an activity
        Act: Try to unregister a student who isn't signed up
        Assert: Verify 400 error
        """
        # Arrange
        activity_name = "Chess Club"
        email = "notstudent@mergington.edu"  # Not in participants
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_from_nonexistent_activity_returns_404(self, client, reset_activities):
        """
        Arrange: Activity that doesn't exist
        Act: Try to unregister from non-existent activity
        Assert: Verify 404 error
        """
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_frees_spot_for_new_signup(self, client, reset_activities):
        """
        Arrange: Activity at capacity, unregister one student to free a spot
        Act: Unregister a student, then sign up a new one
        Assert: Verify the new student can successfully sign up
        """
        # Arrange
        from src.app import activities
        activity_name = "Gym Class"
        activities[activity_name]["max_participants"] = 3  # Set capacity
        activities[activity_name]["participants"] = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Act: Unregister one student
        client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": "student1@mergington.edu"}
        )
        
        # Act: Sign up new student (should succeed)
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        # Assert
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]


class TestEdgeCases:
    """Tests for edge cases and integration scenarios."""
    
    def test_capacity_tracking_accuracy(self, client, reset_activities):
        """
        Arrange: Activity with known capacity and participants
        Act: Query activities endpoint
        Assert: Verify capacity and current participant count
        """
        # Arrange
        activity_name = "Chess Club"
        
        # Act
        response = client.get("/activities")
        activity = response.json()[activity_name]
        spots_left = activity["max_participants"] - len(activity["participants"])
        
        # Assert
        assert activity["max_participants"] == 12
        assert len(activity["participants"]) == 2
        assert spots_left == 10
    
    def test_multiple_operations_sequence(self, client, reset_activities):
        """
        Arrange: Fresh activities state
        Act: Perform signup, then unregister, then signup again
        Assert: Verify all operations succeed and final state is correct
        """
        # Arrange
        activity_name = "Programming Class"
        email = "testuser@mergington.edu"
        
        # Act 1: Sign up
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert 1
        assert response1.status_code == 200
        
        # Act 2: Unregister
        response2 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert 2
        assert response2.status_code == 200
        
        # Act 3: Sign up again
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert 3
        assert response3.status_code == 200
