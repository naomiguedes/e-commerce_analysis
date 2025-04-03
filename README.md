# e-commerce_analysis
E-Commerce Sales Analysis 

This project is a Flask web application designed to show the analysis and visualize e-commerce and retail sales data using Google BigQuery and Plotly. 
The application provides interactive charts to compare sales trends and growth rates, offering insights into sales performance over time.

## Features

- **Data Integration**: Fetches and processes data from Google BigQuery and https://www.census.gov/retail/data.html 
- **Interactive Visualizations**: Utilizes Plotly to create interactive charts for data analysis.
- **Responsive Design**: Incorporates Bootstrap for a responsive and visually appealing interface.

## Installation

### Prerequisites

- Python 3.7 or higher
- Google Cloud SDK
- Access to Google BigQuery
-  **Key Libraries**:
  - **Flask**: Used for building the web application.
  - **Plotly**: Utilized for creating interactive data visualizations.
  - **Google Cloud BigQuery Client**: Used to query and fetch data from BigQuery.

### Usage

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/ecommerce-analysis.git
   cd ecommerce-analysis
2. **Set up virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate
4. **Install dependencies found in requirements file
   ```bash
   pip install -r requirements.txt
6. **Install and authenticate Google Cloud SDK
   ```bash
   gcloud auth application-default login

### Running Instructions
1. **Start the flask application by runnning:
   ```bash
   python app.py
3. **Open a web browser and navigate to http://127.0.0.1:5000/api/sales-analysis-umg/ to view the interactive charts.
   
