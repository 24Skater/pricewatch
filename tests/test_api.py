"""Test API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestTrackerEndpoints:
    """Test tracker-related API endpoints."""
    
    def test_create_tracker_success(self, client, sample_tracker_data):
        """Test successful tracker creation."""
        response = client.post("/trackers", data=sample_tracker_data, follow_redirects=False)
        
        assert response.status_code == 303  # Redirect
        assert "/tracker/" in response.headers["location"]
    
    def test_create_tracker_invalid_data(self, client):
        """Test tracker creation with invalid data."""
        invalid_data = {
            "url": "invalid-url",
            "alert_method": "email",
            "contact": "invalid-email"
        }
        
        response = client.post("/trackers", data=invalid_data)
        # Pydantic validation may return 422 or endpoint may return 400/500
        assert response.status_code in [400, 422, 500]
    
    def test_get_tracker_detail(self, client, sample_tracker):
        """Test getting tracker details."""
        response = client.get(f"/tracker/{sample_tracker.id}")
        
        assert response.status_code == 200
        assert "Test Product" in response.text
    
    def test_get_tracker_not_found(self, client):
        """Test getting non-existent tracker."""
        response = client.get("/tracker/999")
        
        assert response.status_code == 404
    
    def test_delete_tracker(self, client, sample_tracker):
        """Test deleting a tracker."""
        response = client.post(f"/tracker/{sample_tracker.id}/delete", follow_redirects=False)
        
        assert response.status_code == 303
        assert response.headers["location"] == "/"
    
    def test_delete_tracker_not_found(self, client):
        """Test deleting non-existent tracker."""
        response = client.post("/tracker/999/delete")
        
        assert response.status_code == 404


class TestProfileEndpoints:
    """Test profile-related API endpoints."""
    
    def test_create_profile_success(self, client, sample_profile_data):
        """Test successful profile creation."""
        response = client.post("/admin/profiles/new", data=sample_profile_data, follow_redirects=False)
        
        assert response.status_code == 303  # Redirect
        assert response.headers["location"] == "/admin/profiles"
    
    def test_get_profiles_list(self, client, sample_profile):
        """Test getting profiles list."""
        response = client.get("/admin/profiles")
        
        assert response.status_code == 200
        assert "Test Profile" in response.text
    
    def test_get_profile_edit_form(self, client, sample_profile):
        """Test getting profile edit form."""
        response = client.get(f"/admin/profiles/{sample_profile.id}/edit")
        
        assert response.status_code == 200
        assert "Test Profile" in response.text
    
    def test_delete_profile(self, client, sample_profile):
        """Test deleting a profile."""
        response = client.post(f"/admin/profiles/{sample_profile.id}/delete", follow_redirects=False)
        
        assert response.status_code == 303
        assert response.headers["location"] == "/admin/profiles"
    
    def test_profile_update(self, client, sample_profile):
        """Test updating a profile."""
        update_data = {
            "name": "Updated Profile",
            "email_from": "updated@example.com",
            "smtp_host": "smtp.updated.com",
            "smtp_port": "465",
            "smtp_user": "updated_user",
            "smtp_pass": "newpass",
            "csrf_token": "test_token"
        }
        
        response = client.post(
            f"/admin/profiles/{sample_profile.id}/edit",
            data=update_data,
            follow_redirects=False
        )
        
        assert response.status_code == 303
        assert "/admin/profiles" in response.headers["location"]


class TestAPIEndpoints:
    """Test general API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_api_trackers(self, client, sample_tracker):
        """Test API trackers endpoint."""
        response = client.get("/api/trackers")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["url"] == sample_tracker.url
    
    def test_tracker_edit_form(self, client, sample_tracker):
        """Test getting tracker edit form."""
        response = client.get(f"/tracker/{sample_tracker.id}/edit")
        
        assert response.status_code == 200
        assert sample_tracker.url in response.text or "Edit" in response.text
    
    def test_tracker_update(self, client, sample_tracker):
        """Test updating a tracker."""
        update_data = {
            "url": "https://example.com/updated",
            "alert_method": "email",
            "contact": "updated@example.com",
            "name": "Updated Tracker",
            "selector": ".price",
            "profile_id": "0",
            "is_active": "true",
            "poll_now": "0",
            "csrf_token": "test_token"
        }
        
        response = client.post(
            f"/tracker/{sample_tracker.id}/edit",
            data=update_data,
            follow_redirects=False
        )
        
        assert response.status_code == 303
        assert f"/tracker/{sample_tracker.id}" in response.headers["location"]
    
    def test_tracker_update_with_poll_now(self, client, sample_tracker):
        """Test updating tracker with poll_now option."""
        from unittest.mock import patch
        
        with patch('app.services.tracker_service.get_price') as mock_get_price:
            mock_get_price.return_value = (69.99, "USD", "Polled Product")
            
            update_data = {
                "url": "https://example.com/updated",
                "alert_method": "email",
                "contact": "updated@example.com",
                "name": "Updated Tracker",
                "selector": ".price",
                "profile_id": "0",
                "is_active": "true",
                "poll_now": "1",  # Request immediate poll
                "csrf_token": "test_token"
            }
            
            response = client.post(
                f"/tracker/{sample_tracker.id}/edit",
                data=update_data,
                follow_redirects=False
            )
            
            assert response.status_code == 303
            mock_get_price.assert_called()
    
    def test_tracker_set_selector(self, client, sample_tracker):
        """Test setting tracker selector."""
        response = client.post(
            f"/tracker/{sample_tracker.id}/selector",
            data={"selector": ".new-price", "csrf_token": "test_token"},
            follow_redirects=False
        )
        
        assert response.status_code == 303
    
    def test_tracker_refresh(self, client, sample_tracker):
        """Test refreshing tracker price."""
        from unittest.mock import patch
        
        with patch('app.services.tracker_service.get_price') as mock_get_price:
            mock_get_price.return_value = (79.99, "USD", "Updated")
            
            response = client.post(
                f"/tracker/{sample_tracker.id}/refresh",
                data={"csrf_token": "test_token"},
                follow_redirects=False
            )
            
            assert response.status_code == 303
            assert f"/tracker/{sample_tracker.id}" in response.headers["location"]
