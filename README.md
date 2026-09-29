# Ticket Collection System

A premium minimal ticket collection system with admin dashboard, built with Flask and optimized for Vercel deployment.

## Features

- ✨ Clean, minimal UI with premium design
- 🎫 Ticket management and collection
- 📋 Waiting list management
- 📊 Admin dashboard with sorting and filtering
- 📥 Export data to Excel
- 🔍 Real-time search and filtering
- 📱 Fully responsive design
- 🚀 Vercel deployment ready

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/AbdullahAlioo/ticket-collection-system.git
   cd ticket-collection-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   - Home: http://localhost:5000
   - Admin: http://localhost:5000/admin

## API Endpoints

### Add Ticket Data
```
GET /add_data/<email>/<phone>/<name>/<tickets>/<ticket_number>/<country>/<region>
```

**Example:**
```
GET /add_data/john@example.com/+1234567890/John%20Doe/5/TKT001/USA/California
```

### Get All Tickets
```
GET /api/tickets
```

### Add to Waiting List
```
GET /wait/<email>?website=<optional_website>
```

**Example:**
```
GET /wait/user@example.com?website=mywebsite.com
```

### Get Waiting List
```
GET /api/waiting_list
```

### Export to Excel
```
GET /export/excel
```

## Deployment on Vercel

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Framework: Select "Other"
   - Build Command: (leave blank)
   - Output Directory: (leave blank)
   - Install Command: `pip install -r requirements.txt`

3. **Add Environment Variables**
   - SESSION_SECRET: Your secret key

4. **Deploy**
   - Click "Deploy"
   - Your app will be live at `https://your-project.vercel.app`

## File Structure

```
ticket-collection-system/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel configuration
├── README.md             # This file
├── templates/
│   ├── index.html        # Home page
│   └── admin.html        # Admin dashboard
├── static/
│   ├── css/
│   │   └── style.css     # Stylesheet
│   └── js/
│       └── main.js       # JavaScript functionality
└── data/                 # Data storage (JSON files)
```

## Technologies Used

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Data Storage**: JSON files
- **Export**: OpenPyXL (Excel)
- **Deployment**: Vercel

## Security Considerations

- Email and phone validation
- Input sanitization
- CORS headers configured
- Session secret key management

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For issues or questions, please create an issue on the GitHub repository.
