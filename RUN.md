# How to run the C2 server + keylogger

**Important:** Start the **server first**, then the keylogger. If the keylogger runs before the server, POSTs fail silently and nothing appears on the dashboard.

## 1. Start the C2 server (first terminal)

From the **project root** (`-Project-Cerberus`):

```powershell
.\venv\Scripts\Activate.ps1
python red-team\c2-server\server.py
```

Leave it running. You should see: `Running on http://127.0.0.1:5000`.

## 2. Start the keylogger (second terminal)

Open a **new** terminal. From the **project root** again:

```powershell
.\venv\Scripts\Activate.ps1
python red-team\keylogger\keylogger.py
```

Leave it running and type in some window. Data is sent every **10 seconds**, so wait at least 10 seconds before checking the dashboard.

## 3. View captured data

In your browser open: **http://127.0.0.1:5000**

## 4. Stop the keylogger

Press **Esc** in the keylogger terminal. The server can be stopped with **Ctrl+C**.


TWO sited: 
1) http://localhost:5000/ — passive keystroke capture dashboard
2) http://localhost:5000/shell