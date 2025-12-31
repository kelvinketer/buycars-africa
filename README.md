# BuyCars Africa 🚗💨

**BuyCars Africa** is a modern, Kenyan-focused automotive marketplace that connects car buyers directly with trusted dealers. Built with Django, the platform provides a seamless experience for browsing verified vehicles, managing dealership inventories, and facilitating direct communication via WhatsApp and phone.

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![Django](https://img.shields.io/badge/Django-5.0-green.svg)

## 🚀 Features

### **For Buyers**
* **Advanced Search:** Filter vehicles by Make, Body Type, Price Range, Year, and Region (e.g., Nairobi, Mombasa).
* **Rich Vehicle Details:** View high-res galleries, technical specs (Fuel, Transmission, Engine CC), and transparent pricing.
* **Direct Communication:** One-click buttons to **"Chat on WhatsApp"** or **"Call Seller"**.
* **Loan Calculator:** Integrated tool to estimate monthly installments based on deposit and loan tenure.
* **Safety First:** Prominent safety tips to guide first-time buyers.

### **For Dealers (SaaS Dashboard)**
* **Inventory Management:** Add, edit, and delete vehicle listings with ease.
* **Bulk Image Upload:** Upload multiple car photos at once with auto-resize and optimization.
* **Lead Analytics:** Track how many users viewed your cars or clicked to contact you.
* **Showroom Profile:** Dedicated public page displaying all your inventory and contact details.

## 🛠️ Tech Stack

* **Backend:** Python 3, Django 5
* **Database:** PostgreSQL
* **Frontend:** Bootstrap 5, HTML5, CSS3, JavaScript
* **Media Storage:** Cloudinary (Automatic image optimization & CDN)
* **Deployment:** Render / Railway / Heroku

## 📦 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/buycars-africa.git](https://github.com/your-username/buycars-africa.git)
    cd buycars-africa
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory and add the following:
    ```env
    DEBUG=True
    SECRET_KEY=your_secret_key_here
    DATABASE_URL=postgres://user:password@localhost:5432/buycars_db
    CLOUDINARY_CLOUD_NAME=your_cloud_name
    CLOUDINARY_API_KEY=your_api_key
    CLOUDINARY_API_SECRET=your_api_secret
    ```

5.  **Run Migrations**
    ```bash
    python manage.py migrate
    ```

6.  **Create a Superuser**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the Server**
    ```bash
    python manage.py runserver
    ```
    Visit `http://127.0.0.1:8000` in your browser.

## 📸 Screenshots

| Homepage | Vehicle Detail | Dealer Dashboard |
|:---:|:---:|:---:|
| *(Add screenshot here)* | *(Add screenshot here)* | *(Add screenshot here)* |

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!
1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---
*Built with ❤️ for the African Automotive Market.*