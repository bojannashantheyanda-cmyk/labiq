from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import models
import io
import os
import numpy as np
import anthropic
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import r2_score
from dotenv import load_dotenv
from auth import hash_password, verify_password, create_access_token, get_current_user

load_dotenv()

from database import engine, get_db

# Create database tables automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# ── STATIC FILES ──
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("static/index.html")

@app.get("/login")
def login_page():
    return FileResponse("static/login.html")



# ── PYDANTIC MODELS ──
class ExperimentCreate(BaseModel):
    id: str
    category: str
    operator: str
    date: str
    notes: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

# ── AUTH ENDPOINTS ──
@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer", "username": db_user.username}

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = create_access_token({"sub": db_user.username})
    return {"access_token": token, "token_type": "bearer", "username": db_user.username}

@app.get("/me")
def get_me(current_user: models.User = Depends(get_current_user)):
    return {"username": current_user.username, "email": current_user.email}

# ── EXPERIMENTS ──
@app.get("/experiments")
def get_experiments(db: Session = Depends(get_db)):
    return db.query(models.Experiment).all()

@app.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str, db: Session = Depends(get_db)):
    exp = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return exp

@app.post("/experiments")
def create_experiment(experiment: ExperimentCreate, db: Session = Depends(get_db)):
    db_exp = models.Experiment(**experiment.dict())
    db.add(db_exp)
    db.commit()
    db.refresh(db_exp)
    return db_exp

@app.delete("/experiments/{experiment_id}")
def delete_experiment(experiment_id: str, db: Session = Depends(get_db)):
    exp = db.query(models.Experiment).filter(models.Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    db.delete(exp)
    db.commit()
    return {"message": f"Experiment {experiment_id} deleted"}

# ── IMPORT ──
@app.post("/import")
async def import_experiments(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    elif file.filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(contents))
    else:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    required = ["id", "category", "operator", "date"]
    for col in required:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing column: {col}")
    imported = 0
    skipped = 0
    for _, row in df.iterrows():
        existing = db.query(models.Experiment).filter(
            models.Experiment.id == str(row["id"])
        ).first()
        if existing:
            skipped += 1
            continue
        exp = models.Experiment(
            id=str(row["id"]),
            category=str(row["category"]),
            operator=str(row["operator"]),
            date=str(row["date"]),
            notes=str(row.get("notes", "")) if pd.notna(row.get("notes", "")) else ""
        )
        db.add(exp)
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped, "total_rows": len(df)}

# ── ANALYTICS ──
@app.get("/analytics/{experiment_id}")
def get_experiment_data(experiment_id: str):
    filepath = f"data/{experiment_id}_data.csv"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"No data file found for {experiment_id}")
    df = pd.read_csv(filepath)
    return {
        "experiment_id": experiment_id,
        "rows": len(df),
        "columns": list(df.columns),
        "stats": df.describe().round(3).to_dict(),
        "data": df.to_dict(orient="records")
    }

# ── REGRESSION & FORECASTING ──
@app.get("/regression/{experiment_id}")
def get_regression(experiment_id: str, x_col: str = "index", y_col: str = "temperature_C", degree: int = 1):
    filepath = f"data/{experiment_id}_data.csv"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"No data file found for {experiment_id}")
    df = pd.read_csv(filepath).reset_index()
    df['index'] = df.index
    if x_col not in df.columns or y_col not in df.columns:
        raise HTTPException(status_code=400, detail="Column not found")
    data = df[[x_col, y_col]].dropna()
    X = data[x_col].values.reshape(-1, 1)
    y = data[y_col].values
    poly = PolynomialFeatures(degree=degree)
    X_poly = poly.fit_transform(X)
    model = LinearRegression()
    model.fit(X_poly, y)
    y_pred = model.predict(X_poly)
    r2 = r2_score(y, y_pred)
    x_max = float(X.max())
    x_future = np.linspace(0, x_max * 1.2, 120).reshape(-1, 1)
    X_future_poly = poly.transform(x_future)
    y_future = model.predict(X_future_poly)
    return {
        "experiment_id": experiment_id,
        "x_col": x_col,
        "y_col": y_col,
        "degree": degree,
        "r2_score": round(r2, 4),
        "actual": {"x": X.flatten().tolist(), "y": y.tolist()},
        "fitted": {"x": X.flatten().tolist(), "y": y_pred.tolist()},
        "forecast": {"x": x_future.flatten().tolist(), "y": y_future.tolist()},
        "equation": f"Degree-{degree} polynomial fit | R² = {round(r2, 4)}"
    }

# ── CORRELATION ──
@app.get("/correlation/{experiment_id}")
def get_correlation(experiment_id: str):
    filepath = f"data/{experiment_id}_data.csv"
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"No data file found for {experiment_id}")
    df = pd.read_csv(filepath)
    numeric_df = df.select_dtypes(include=[np.number])
    corr = numeric_df.corr().round(3)
    return {
        "columns": list(corr.columns),
        "matrix": corr.values.tolist()
    }

# ── AI QUERY ──
@app.post("/ai-query")
async def ai_query(request: dict, db: Session = Depends(get_db)):
    question = request.get("question", "")
    experiment_id = request.get("experiment_id", "")
    data_context = ""
    if experiment_id:
        filepath = f"data/{experiment_id}_data.csv"
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            stats = df.describe().round(3).to_string()
            data_context = f"\n\nExperiment {experiment_id} data summary:\n{stats}"
    experiments = db.query(models.Experiment).all()
    exp_list = "\n".join([f"- {e.id}: {e.category}, operator {e.operator}, date {e.date}, notes: {e.notes}" for e in experiments])
    system_prompt = f"""You are LabIQ, an intelligent lab data assistant.
You have access to the following experiments:
{exp_list}
{data_context}
Answer questions about the lab data concisely and scientifically.
Keep answers under 150 words."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{"role": "user", "content": question}],
        system=system_prompt
    )
    return {"answer": message.content[0].text, "question": question}

# ── UPLOAD DATA FILE ──
@app.post("/upload-data/{experiment_id}")
async def upload_data_file(experiment_id: str, file: UploadFile = File(...)):
    allowed = [".csv", ".xlsx", ".xls"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    save_path = f"data/{experiment_id}_data{ext}"
    contents = await file.read()
    with open(save_path, "wb") as f:
        f.write(contents)
    try:
        if ext == ".csv":
            df = pd.read_csv(save_path)
        else:
            df = pd.read_excel(save_path)
        rows = len(df)
        cols = list(df.columns)
    except Exception as e:
        os.remove(save_path)
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")
    return {
        "message": f"Data file uploaded successfully for {experiment_id}",
        "rows": rows,
        "columns": cols,
        "saved_as": save_path
    }