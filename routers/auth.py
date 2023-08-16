from datetime import datetime
from typing import Annotated
from datetime import timedelta
from database import SessionLocal
from fastapi import APIRouter, Depends, status, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/login')

router = APIRouter(
    prefix='/auth',
    tags=['auth'],
    )


SECRET_KEY = '9igu83ruwzhg4938h323y3hzu'
ALGORITHM = 'HS256'

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# single- Depends
# multiple-

db_dependancy = Annotated[Session, Depends(get_db)]

def authenticate_user(username: str, plain_password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(plain_password, user.hashed_password):
        return False
    return user

class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    class Config:
        json_schema_extra = {
            'example': {
                'username': 'adityasrikarchas',
                'email': 'mrbean1362@gmail.com',
                'first_name': 'aditya',
                'last_name': 'srikar',
                'password': '12345678',
                'role': 'user'
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependancy, create_user_request: CreateUserRequest = Body()):
    create_user_model = Users(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.last_name,
        last_name = create_user_request.last_name,
        role = create_user_request.role,
        hashed_password = bcrypt_context.hash(create_user_request.password),
        is_active = True
    )
    db.add(create_user_model)
    db.commit()

def create_access_token(username: str, user_id: int, role: str, expiry_duration: timedelta):
    expires_at = datetime.utcnow() + expiry_duration
    encode = {'name': username, 'id': user_id, 'role': role, 'exp': expires_at}
    return jwt.encode(claims=encode, key=SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('name')
        user_id: int = payload.get('id')
        role: str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user')
        return {'username': username, 'id': user_id, 'role': role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user')


@router.post('/login', response_model=Token)
async def login_for_acess_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependancy):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Failed Authentication')

    token = create_access_token(username=user.username, user_id=user.id, role=user.role, expiry_duration=timedelta(minutes=10))
    return {'access_token': token, 'token_type': 'bearer'}

# USER ENTERS APPLICATION
# AT CLIENT SIDE, CHECK IF JWT IS PRESENT AND IT SHOULD BE VALID
# IF IT IS NOT FOUND OR NOT VALID, WE HAVE TO PROMPT USER TO LOG IN
# THE USER ENTERS CREDENTIALS
# END POINT IS HIT AT BACKEND SERVER
# VALIDATE USER CREDENTIALS & CREATE JWT with expiry time
# RETURN JWT TO CLIENT SIDE
# SAVE JWT EITHER IN COOKIE