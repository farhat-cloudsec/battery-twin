import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import mean_absolute_error
import joblib

CELL_ID = "B0005"  # which NASA cell to train on
DATA_PATH = "twin/data/nasa_battery_capacity_vs_cycle.csv"

df = pd.read_csv(DATA_PATH)
df = df[df["cell_id"] == CELL_ID].sort_values("cycle")

nominal_capacity = df["capacity_ah"].iloc[0]  # capacity at cycle 1, used as the "new" baseline
df["soh_percent"] = (df["capacity_ah"] / nominal_capacity) * 100

X = df[["cycle"]]
y = df["capacity_ah"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

with mlflow.start_run(run_name=f"soh_model_{CELL_ID}"):
    degree = 2
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)

    mlflow.log_param("model_type", "PolynomialRegression")
    mlflow.log_param("degree", degree)
    mlflow.log_param("cell_id", CELL_ID)
    mlflow.log_param("nominal_capacity_ah", nominal_capacity)
    mlflow.log_metric("mae_ah", mae)
    mlflow.sklearn.log_model(model, "model")

    print(f"Trained SoH model on NASA cell {CELL_ID}.")
    print(f"MAE on test set: {mae:.5f} Ah")
    print(f"That's about {mae / nominal_capacity * 100:.2f}% of nominal capacity.")

joblib.dump({"model": model, "nominal_capacity": nominal_capacity}, "twin/soh_model.joblib")
print("Model saved to twin/soh_model.joblib")