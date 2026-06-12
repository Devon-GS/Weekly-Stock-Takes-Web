# Coffee Shop Weekly Stock Takes

A web-based inventory management and stock-take system designed specifically for coffee shops. This application automates the calculation of ingredient usage (milk, beans, sugar) and bakery supplies by comparing physical stock counts against imported sales and purchase data.

## 🚀 Features

### ☕ Coffee & Milk Tracking
*   **Milk Usage:** Calculate ml-per-cup usage by tracking 2L, 1L, and 500ml containers.
*   **Bean Coffee:** Track specific drink types (Americano, Latte, etc.) and calculate consumption.
*   **Lavazza & Sugar:** Specialized tracking for branded coffee and sweetener usage/purchases.

### 🥐 Bakery Management
*   **Dough Tracking:** Manage ingredients for pizza and normal dough (flour, yeast, oil, sugar, salt).
*   **Component Tracking:** Monitor inventory for Egg Wash, Mayo, and Sweet Chilli.
*   **Sales Integration:** Automatically pulls "Pies Sold" or "Pizzas Sold" from CSV data to calculate theoretical usage.

### 📊 Data Integration
*   **CSV Import:** Import Sales and Purchase reports from your Point of Sale (POS) system.
*   **Smart Mapping:** Define custom keywords in Settings (e.g., "Latte" or "Flat White") to automatically sum quantities from CSV files.
*   **Automated Calculations:** Automatically determines quantities sold between two stock-take dates.

---

## 🛠️ Technology Stack
*   **Backend:** Python / Flask
*   **Database:** SQLite
*   **Frontend:** HTML5, JavaScript (Fetch API)
*   **Deployment:** Docker / Gunicorn

---

## 📦 Installation (Local)

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd weekly-stock-takes
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```
    The app will be available at `http://localhost:5000`.

---

## 🐳 Deployment (Docker)

This application is containerized for easy deployment.

### Using Docker Compose
1.  **Build and start the container:**
    ```bash
    docker-compose up -d --build
    ```

### Using Docker CLI
1.  **Build the image:**
    ```bash
    docker build -t coffee-stock-takes .
    ```
2.  **Run the container:**
    ```bash
    docker run -d -p 5001:5001 --name stock-takes coffee-stock-takes
    ```

---

## 📑 CSV Format Guide

To use the automated sales and purchase tracking, ensure your CSV files follow this structure:

### Sales CSV
*   **Column 2 (Index 1):** Product Description (e.g., "Cappuccino Large")
*   **Column 4 (Index 3):** Date (DD/MM/YYYY or YYYY-MM-DD)
*   **Column 7 (Index 6):** Quantity Sold

### Purchases CSV
*   **Column 1 (Index 0):** Product Description (e.g., "Cake Flour 10kg")
*   **Column 7 (Index 6):** Quantity Purchased

---

## ⚙️ Configuration

1.  **Import Data:** Go to the **Import** page and upload your latest Sales and Purchases CSV files.
2.  **Map Products:** Go to **Settings**. Add keywords for each category. 
    *   *Example:* For "Milk Coffee", add "Latte", "Cappuccino", and "Flat White". 
    *   The system will now sum any sales item containing those words when calculating coffee sold.
3.  **Weights:** Configure the grams per unit for sugar and sweeteners to get accurate usage reports.

---

## 📂 Project Structure

```text
├── app.py              # Main Flask application logic & API routes
├── Database/           # SQLite database storage (stocktakes.db)
├── static/             # CSS, JS, and Images
├── templates/          # HTML Templates
│   ├── bakery/         # Bakery-specific views
│   ├── index.html      # Dashboard
│   └── ...
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
└── requirements.txt    # Python dependencies
```

---