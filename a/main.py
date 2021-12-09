from pydantic import BaseModel
from sqlalchemy.engine import create_engine
from datetime import datetime as d
import datetime
import uvicorn
from typing import List,Optional
from sqlalchemy.sql import text
import pandas as pd
import io
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, select, MetaData, Table, and_, or_
from datetime import  timedelta
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel,SecretStr

# creating a FastAPI server
server = FastAPI(title='International football matches')

# creating a connection to the database
mysql_url = 'a_dataBase_1'  # to complete
mysql_user = 'root'
mysql_password = 'supersecret'  # to complete
database_name = 'INTERNATIONAL_RESULTS'

# recreating the URL connection
connection_url = 'mysql://{user}:{password}@{url}/{database}'.format(
    user=mysql_user,
    password=mysql_password,
    url=mysql_url,
    database=database_name
)

# creating the connection
mysql_engine = create_engine(connection_url)

metadata = MetaData(bind=None)
table_res = Table('RESULTS',metadata,autoload=True,autoload_with=mysql_engine)
table_sh = Table('SHOOTOUTS',metadata,autoload=True,autoload_with=mysql_engine)

# creating a Match class
class Match(BaseModel):

    date: datetime.date
    home_team: str = 'France'
    away_team: str = 'Italy'
    home_score: int = 0
    away_score: int = 0
    tournament: str = 'Friendly'
    city: str = 'Paris'
    country: str = 'France'
    neutral: int = 0

# creating a Match shootout class
class Match_shootout(BaseModel):

    date: datetime.date
    home_team: str = 'France'
    away_team: str = 'Italy'
    home_score: int = 0
    away_score: int = 0
    tournament: str = 'Friendly'
    city: str = 'Paris'
    country: str = 'France'
    neutral: int = 0
    shootout_winner: str

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "f00082b84c35f4c1b1d23efee9234c70e5a77059872fb08b271405aabbbdaafc"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

c = '\r'

with mysql_engine.connect() as connection:
     results = connection.execute('SELECT Username, trim(both "{c}" from Password) as Password FROM CREDENTIALS;'.format(c=c))
     fake_users_db = { i[0]: {
            'username': i[0],
            'hashed_password': i[1],
            'disabled': False }
             for i in results.fetchall() }


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = d.utcnow() + expires_delta
    else:
        expire = d.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@server.post("/token",include_in_schema=False, response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}




@server.get('/status')
async def get_status():
    """Returns 1
    """
    return 1


@server.get('/matches')
async def get_matches():

    with mysql_engine.connect() as connection:
        results = connection.execute('SELECT * FROM RESULTS ORDER BY date DESC LIMIT 10;')

    results = [
        Match(
            date= i[1],
            home_team=i[2],
            away_team=i[3],
            home_score=i[4],
            away_score=i[5],
            tournament=i[6],
            city=i[7],
            country=i[8],
            neutral=i[9],
            ) for i in results.fetchall()]

    return results


@server.get('/matches/{team:str,n:int}', response_model=List[Match],tags = ['Last n matches'])
async def get_last_n_matches(team,n):

    q= table_res.select().where(or_(table_res.columns.home_team == team, table_res.columns.away_team == team )).order_by(table_res.columns.date.desc()).limit(n)

    connection = mysql_engine.connect()
    results = connection.execute(q)

    results = [
        Match(
            date= i[1],
            home_team=i[2],
            away_team=i[3],
            home_score=i[4],
            away_score=i[5],
            tournament=i[6],
            city=i[7],
            country=i[8],
            neutral=i[9],
            ) for i in results.fetchall()]

    if len(results) == 0:
        raise HTTPException(
            status_code=404,
            detail='Unknown team')
    else:

        return results


@server.post('/matches_csv/{team:str, n:int}', response_model=List[Match],tags = ['Last n matches'])
async def get_last_n_matches_csv(team,n, current_user: User = Depends(get_current_active_user)):

    q= table_res.select().where(or_(table_res.columns.home_team == team, table_res.columns.away_team == team )).order_by(table_res.columns.date.desc()).limit(n)

    connection = mysql_engine.connect()
    results = connection.execute(q).fetchall()

    df = pd.DataFrame(results)

    df.columns = table_res.columns.keys()

    stream = io.StringIO()


    df.to_csv(stream)

    response = StreamingResponse(iter([stream.getvalue()]),
                            media_type="text/csv"
        )

    response.headers["Content-Disposition"] = "attachment; filename=last_n_matches.csv"

    if len(results) == 0:
        raise HTTPException(
            status_code=404,
            detail='Unknown team')
    else:

        return response


@server.post('/insert_match_csv/{date: date.datetime, home_team: str , away_team: str , home_score: int , away_score: int , tournament: str, city: str, country: str, neutral: int  }', response_model=List[Match],tags = ['Insert new match'])
async def insert_get_new_csv(date, home_team, away_team, home_score , away_score , tournament, city, country, neutral, current_user: User = Depends(get_current_active_user)):

    date = pd.to_datetime(date)

    mysql_engine.execute(table_res.insert(), date=datetime.date(date.year, date.month, date.day), home_team= home_team , away_team= away_team , home_score= home_score , away_score= away_score , tournament= tournament, city=city, country=country, neutral=neutral)

    q= table_res.select()

    connection = mysql_engine.connect()
    results = connection.execute(q).fetchall()

    df = pd.DataFrame(results)

    df.columns = table_res.columns.keys()

    stream = io.StringIO()


    df.to_csv(stream)

    response = StreamingResponse(iter([stream.getvalue()]),
                            media_type="text/csv"
        )

    response.headers["Content-Disposition"] = "attachment; filename=results.csv"

    if len(results) == 0:
        raise HTTPException(
            status_code=404,
            detail='Unknown')
    else:

        return response


@server.get('/matches_shootouts/{team:str,n:int}', response_model=List[Match_shootout], tags = ['Last n matches with shootouts'])
async def get_matches(team,n):

    with mysql_engine.connect() as connection:
        results = connection.execute(
        '''SELECT r.*, s.winner
        FROM RESULTS r
        INNER JOIN SHOOTOUTS s
        ON r.date=s.date AND r.home_score=r.away_score AND r.home_team=s.home_team AND r.away_team=s.away_team
        WHERE (r.home_team LIKE "{a}" or r.away_team LIKE "{a}")
        ORDER BY r.date DESC
        LIMIT {b};'''.format(a=team,b=n))

    results = [
        Match_shootout(
            date= i[1],
            home_team=i[2],
            away_team=i[3],
            home_score=i[4],
            away_score=i[5],
            tournament=i[6],
            city=i[7],
            country=i[8],
            neutral=i[9],
            shootout_winner=i[10],
            )  for i in results.fetchall()]

    if len(results) == 0:
        raise HTTPException(
            status_code=404,
            detail='Unknown team')
    else:

        return results


@server.get('/matches_year/{team:str, year_date: int }', response_model=List[Match], tags = ['Get matches year'])
async def get_matches_year(team,year_date):

    with mysql_engine.connect() as connection:
        results = connection.execute(
        '''SELECT * FROM RESULTS
        WHERE (home_team LIKE "{a}" or away_team LIKE "{a}") and YEAR(date) = {b}
        ORDER BY date DESC
        ;'''.format(a=team, b=year_date))

    results = [
        Match(
            date= i[1],
            home_team=i[2],
            away_team=i[3],
            home_score=i[4],
            away_score=i[5],
            tournament=i[6],
            city=i[7],
            country=i[8],
            neutral=i[9]
            )  for i in results.fetchall()]

    if len(results) == 0:
        raise HTTPException(
            status_code=404,
            detail='Unknown team')
    else:

        return results




if __name__ == "__main__":
    uvicorn.run(server, host="0.0.0.0", port=8000)



#from passlib.context import CryptContext

#pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#pwd_context.hash("")
