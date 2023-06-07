#This API was developed by Alex Mutonga
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app import models
from app.routers import customers, auth, laundromat, courier, admins, lockers, payment, orders
from .database import engine
#from .routers import post, user, auth, vote
from .config import settings   
from .routers import auth


print(settings)

models.Base.metadata.create_all(bind=engine) 
#uses sqlachemy to create tables for you
#you might not need it any longer as  ALEMBIC will auto generate tables for you


app = FastAPI()

origins = ["*"] #You should connect only to your damain during deployment *(security best practices)*

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(customers.router)
app.include_router(laundromat.router)
app.include_router(auth.router)
app.include_router(courier.router)
app.include_router(admins.router)
app.include_router(lockers.router)
app.include_router(payment.router)
app.include_router(orders.router)

@app.get("/")
async def root():
    return {"Welcome to Smart launders"}
