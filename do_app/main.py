from typing import Annotated
from fastapi import  FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from do_app import settings
from contextlib import asynccontextmanager

# Create Model
    #data model      #table model
class Todo (SQLModel, table = True):
    id : int | None = Field(default = None, primary_key = True)
    content : str = Field(index = True, min_length=3, max_length= 54)
    is_completed : bool = Field(default = False)

#engine is one for whole application
connection_string :str = str(settings.DATABASE_URL).replace("postgresql", "postgresql+psycopg")
engine = create_engine(connection_string, connect_args= {"sslmode" : "require"}, pool_recycle=300, pool_size = 10, echo =True)


def create_tables():
    SQLModel.metadata.create_all(engine)


#session: separate for each functionality/transaction

def get_session():
    with Session(engine) as session:
        yield session

@asynccontextmanager
async def lifespan(app:FastAPI):
    print('Creating Tables')
    create_tables()
    print("Tables Created")
    yield

app: FastAPI = FastAPI(lifespan =lifespan, title = "To Do App", version="1.0.0")

@app.get('/')
async def root():
    return {"msg" : "Welcome to daily todo app"}

@app.post('/todos/', response_model = Todo)
async def create_todo(todo:Todo, session : Annotated[Session, Depends(get_session)]):
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo

@app.get('/todos/', response_model = list[Todo])
async def get_all(session : Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo)).all()
    if todos:
     return todos
    else :
        raise HTTPException (status_code= 404, detail= "No Task Found")

@app.get('/todos/{id}', response_model = Todo)
async def get_single_todo(id:int, session : Annotated[Session, Depends(get_session)]):
    todos = session.exec(select(Todo).where(Todo.id==id)).first()
    if todos:
        return todos
    else :
        raise HTTPException (status_code= 404, detail= "No Task Found")

    

@app.put('/todos/{id}')
async def edit_todo(id:int, todo: Todo, session : Annotated[Session, Depends(get_session)]):
    existing_todo = session.exec(select(Todo).where(Todo.id==id)).first()
    if existing_todo:
        existing_todo.content = todo.content
        existing_todo.is_completed = todo.is_completed
        session.add(existing_todo)
        session.commit()
        session.refresh(existing_todo)
        return existing_todo
    else:
        raise HTTPException (status_code= 404, detail= "No Task Found")

@app.delete('/todos/{id}')
async def delete_todo(id:int, session : Annotated[Session, Depends(get_session)]):
    todo = session.get(Todo, id)
    if todo:
        session.delete(todo)
        session.commit()
        return {"message" : "Task Successfully Deleted"}
    else :
        raise HTTPException (status_code= 404, detail= "No Task Found")
