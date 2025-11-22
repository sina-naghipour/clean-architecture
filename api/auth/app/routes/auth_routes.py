from fastapi import APIRouter, Request

router = APIRouter(prefix='auth', tags=['auth'])

@router.post('/register')
def register_user(request: Request):
    pass

router.post('/login')
def login_user(request: Request):
    pass

router.get('/me')
def return_current_user():
    pass

router.post('/refresh')
def refresh_token():
    pass

router.post('/logout')
def logout():
    pass