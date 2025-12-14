# FastAPI Backend Project

This is a FastAPI backend project. It provides APIs for your application and can be run locally for development or deployed to a server.

**Python Version:** 3.11.9

---

## **Clone the Project**

```bash
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

---

## **Set Up a Virtual Environment**

It is recommended to use a virtual environment to manage dependencies:

```bash
python -m venv .venv
```

Activate the virtual environment:

- **Windows:**

```bash
.venv\Scripts\activate
```

- **Linux / macOS:**

```bash
source .venv/bin/activate
```

---

## **Install Dependencies**

Install all required Python packages using `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## **Run the FastAPI Server**

Start the server using Uvicorn with auto-reload:

```bash
uvicorn main:app --reload
```

- The server will run at `http://127.0.0.1:8000`
- Interactive API documentation:

  - Swagger UI: `http://127.0.0.1:8000/docs`
  - Redoc: `http://127.0.0.1:8000/redoc`

---

## **Project Structure Example**

```
my_fastapi_project/
├─ app/
│  ├─ main.py
│  ├─ routers/
│  ├─ models/
│  ├─ utils/
│  └─ services/
├─ .venv/
├─ .env
├─ .env.example
├─ requirements.txt
└─ README.md
```

---

## **Notes**

- Make sure `venv/` is added to `.gitignore` to avoid committing your virtual environment.
- Use `pip freeze > requirements.txt` to update dependencies after installing new packages.
- FastAPI automatically generates interactive API docs at `/docs` and `/redoc`.

---

## **License**

MIT License

Copyright (c) 2025 CADT Face Recognition Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

---
