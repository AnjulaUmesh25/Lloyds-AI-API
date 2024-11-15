import numpy as np
import pandas as pd
import uvicorn

from typing import Union
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import ValidationError
import logging
from datetime import datetime, timedelta


from request_model import RequestPayload
from ml_model.lloyds_predictor import model

# Initialize the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

#############################################################
#############################################################

from fastapi.security import OAuth2PasswordRequestForm
from security.auth2 import (Token, authenticate_user, db,
                            ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, 
                            User, get_current_active_user)
## Authentication System (OAuth2 with JWT)
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

#############################################################
#############################################################

## Check Health
@app.get("/root")
def read_root():
    return {"Hello": "World"}


## Risk Prediction Endpoint (Protected by JWT Authentication)
@app.post("/risk", tags=['Main'])
async def lloyds_predictor(payload: RequestPayload,
                           token:User = Depends(get_current_active_user)):
    try:
        output = model(payload.dict())
        return {"Status": output}
    except HTTPException as e:
        raise e


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)