# 🌾 AgriPredict — Crop Yield Prediction System

AgriPredict is a machine learning-based web application that predicts agricultural crop yield using input parameters such as crop, region, district, year, temperature, and rainfall. It also displays estimated profit based on the application's prediction logic.

## 🚀 Features

- Crop yield prediction using a trained machine learning model
- District and region-based inputs
- Temperature, rainfall, and year as prediction parameters
- Estimated profit display
- Simple web interface built with Flask
- Online deployment using Render

## 🛠️ Technologies Used

- **Programming Language:** Python
- **Machine Learning:** Scikit-learn
- **Data Processing:** Pandas, NumPy
- **Web Framework:** Flask
- **Model Serialization:** Joblib
- **Deployment:** Render
- **Version Control:** Git and GitHub

## ⚙️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/adityasonawane-source/AgriPredict.git
cd AgriPredict
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

```bash
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

## 📊 Machine Learning Model

AgriPredict uses a trained Scikit-learn pipeline to estimate crop yield from agricultural input data.

**Input features:**
- Crop
- Region
- District
- Year
- Temperature
- Rainfall

**Output:** Predicted crop yield and estimated profit.

Model predictions are estimates and should not be treated as guaranteed agricultural outcomes.

## 🌐 Live Demo

[Open AgriPredict]https://(agripredict-xikn.onrender.com)

## 📂 Project Structure

```text
AgriPredict/
├── app.py
├── common.py
├── services.py
├── train.py
├── model_district.joblib
├── requirements.txt
├── README.md
├── data/
└── static/
```

## 🔮 Future Improvements

- Add more weather and soil parameters
- Improve model accuracy using additional agricultural datasets
- Add interactive charts for crop yield trends
- Improve the user interface for mobile devices
- Provide crop-wise comparisons and decision support

## 👨‍💻 Author

**Aditya Sonawane**

GitHub: [adityasonawane-source](https://github.com/adityasonawane-source)

LinkedIn: [Aditya Sonawane](https://www.linkedin.com/in/aditya-sonawane-8999828720c)

---

*AgriPredict — Using machine learning to support data-driven agricultural decisions.*

