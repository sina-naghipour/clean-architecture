from .profile_helpers import create_problem_response
from fastapi import Request
from fastapi.responses import JSONResponse
from database import models

class ProfileService:
    def __init__(self, logger):
        self.logger = logger
        self.profiles = {}
        self.addresses = {}
        self.next_address_id = 1
        
        # Initialize mock data
        self._initialize_mock_data()

    def _initialize_mock_data(self):
        # Mock user profile
        self.profiles["user_123"] = {
            'id': 'user_123',
            'email': 'alice@example.com',
            'name': 'Alice',
            'phone': '+1234567890',
            'password': 'hashed_password_123'
        }
        
        # Mock addresses
        self.addresses["user_123"] = [
            {
                'id': 'addr_1',
                'line': '123 Main St',
                'city': 'New York',
                'postal_code': '10001',
                'country': 'USA'
            }
        ]
        
        self.next_address_id = 1

    async def get_profile(
        self,
        request: Request,
        user_id: str,
    ):
        self.logger.info(f"Profile retrieval attempt for user: {user_id}")
        
        profile_data = self.profiles.get(user_id)
        
        if not profile_data:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Profile not found",
                instance=str(request.url)
            )
        
        profile = models.UserResponse(
            id=profile_data['id'],
            email=profile_data['email'],
            name=profile_data['name']
        )
        
        self.logger.info(f"Profile retrieved successfully for user: {user_id}")
        return profile

    async def update_profile(
        self,
        request: Request,
        profile_data: models.ProfileUpdate,
        user_id: str,
    ):
        self.logger.info(f"Profile update attempt for user: {user_id}")
        
        existing_profile = self.profiles.get(user_id)
        if not existing_profile:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Profile not found",
                instance=str(request.url)
            )
        
        # Update only provided fields
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                existing_profile[field] = value
        
        updated_profile = models.UserResponse(
            id=existing_profile['id'],
            email=existing_profile['email'],
            name=existing_profile['name']
        )
        
        self.logger.info(f"Profile updated successfully for user: {user_id}")
        return updated_profile

    async def change_password(
        self,
        request: Request,
        password_data: models.PasswordChange,
        user_id: str,
    ):
        self.logger.info(f"Password change attempt for user: {user_id}")
        
        existing_profile = self.profiles.get(user_id)
        if not existing_profile:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Profile not found",
                instance=str(request.url)
            )
        
        # Mock password validation - in real app, you'd hash and compare
        if password_data.old_password != "current_password":
            return create_problem_response(
                status_code=400,
                error_type="bad-request",
                title="Bad Request",
                detail="Current password is incorrect",
                instance=str(request.url)
            )
        
        # Update password (in real app, you'd hash it)
        existing_profile['password'] = f"hashed_{password_data.new_password}"
        
        self.logger.info(f"Password changed successfully for user: {user_id}")
        return {"message": "Password updated successfully"}

    async def list_addresses(
        self,
        request: Request,
        user_id: str,
    ):
        self.logger.info(f"Addresses listing attempt for user: {user_id}")
        
        user_addresses = self.addresses.get(user_id, [])
        
        addresses_response = [
            models.AddressResponse(
                id=addr['id'],
                line=addr['line'],
                city=addr['city'],
                postal_code=addr['postal_code'],
                country=addr['country']
            ) for addr in user_addresses
        ]
        
        self.logger.info(f"Addresses listed successfully for user: {user_id}")
        return addresses_response

    async def create_address(
        self,
        request: Request,
        address_data: models.AddressRequest,
        user_id: str,
    ):
        self.logger.info(f"Address creation attempt for user: {user_id}")
        
        if user_id not in self.addresses:
            self.addresses[user_id] = []
        
        address_id = f"addr_{self.next_address_id}"
        new_address = {
            'id': address_id,
            'line': address_data.line,
            'city': address_data.city,
            'postal_code': address_data.postal_code,
            'country': address_data.country
        }
        
        self.addresses[user_id].append(new_address)
        self.next_address_id += 1
        
        address_response = models.AddressResponse(
            id=new_address['id'],
            line=new_address['line'],
            city=new_address['city'],
            postal_code=new_address['postal_code'],
            country=new_address['country']
        )
        
        self.logger.info(f"Address created successfully: {address_id}")
        
        response = JSONResponse(
            status_code=201,
            content=address_response.model_dump(),
            headers={"Location": f"/api/profile/addresses/{address_id}"}
        )
        return response

    async def update_address(
        self,
        request: Request,
        address_id: str,
        address_data: models.AddressRequest,
        user_id: str,
    ):
        self.logger.info(f"Address update attempt: {address_id}")
        
        user_addresses = self.addresses.get(user_id, [])
        address_to_update = None
        address_index = -1
        
        for i, addr in enumerate(user_addresses):
            if addr['id'] == address_id:
                address_to_update = addr
                address_index = i
                break
        
        if not address_to_update:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Address not found",
                instance=str(request.url)
            )
        
        # Update address
        updated_address = {
            'id': address_id,
            'line': address_data.line,
            'city': address_data.city,
            'postal_code': address_data.postal_code,
            'country': address_data.country
        }
        
        self.addresses[user_id][address_index] = updated_address
        
        address_response = models.AddressResponse(
            id=updated_address['id'],
            line=updated_address['line'],
            city=updated_address['city'],
            postal_code=updated_address['postal_code'],
            country=updated_address['country']
        )
        
        self.logger.info(f"Address updated successfully: {address_id}")
        return address_response

    async def delete_address(
        self,
        request: Request,
        address_id: str,
        user_id: str,
    ):
        self.logger.info(f"Address deletion attempt: {address_id}")
        
        user_addresses = self.addresses.get(user_id, [])
        address_to_delete = None
        
        for i, addr in enumerate(user_addresses):
            if addr['id'] == address_id:
                address_to_delete = addr
                break
        
        if not address_to_delete:
            return create_problem_response(
                status_code=404,
                error_type="not-found",
                title="Not Found",
                detail="Address not found",
                instance=str(request.url)
            )
        
        # Remove address
        self.addresses[user_id] = [addr for addr in user_addresses if addr['id'] != address_id]
        
        self.logger.info(f"Address deleted successfully: {address_id}")
        return JSONResponse(status_code=204, content=None)
