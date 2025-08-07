# Data Quality Pipeline with Power BI Integration

A comprehensive data quality analysis platform with AI-powered anomaly detection and seamless Power BI integration for enterprise-grade data insights.

## Features

### Core Functionality
- **Multi-Source Data Connectivity**: Connect to PostgreSQL, MySQL, SQL Server databases, and CSV file uploads
- **5-Dimensional Quality Analysis**: Comprehensive data quality metrics including completeness, validity, consistency, uniqueness, and accuracy
- **AI-Powered Anomaly Detection**: VARIMA (Vector Autoregressive Integrated Moving Average) models for multivariate anomaly detection
- **Power BI Integration**: Automated dashboard generation with downloadable packages
- **Real-time Analysis**: Live data quality monitoring and caching for improved performance
- **Export Capabilities**: CSV exports with detailed statistics and quality metrics

### Technical Architecture
- **Backend**: FastAPI with modular architecture for scalability and maintainability
- **Frontend**: Next.js with TypeScript and modern UI components
- **Database Support**: PostgreSQL, MySQL, SQL Server with SQLAlchemy ORM
- **Caching**: Redis for performance optimization and session management
- **Analytics**: Advanced statistical analysis with pandas and numpy
- **Visualization**: Power BI integration for enterprise dashboards

## Project Structure

```
power-bi-dashboard-setup/
├── backend/                 # FastAPI backend services
│   ├── main.py             # Application entry point
│   ├── models.py           # Pydantic data models
│   ├── routes.py           # API endpoint definitions
│   ├── database.py         # Database connection utilities
│   ├── analysis.py         # Data quality analysis engine
│   ├── export.py           # Export and Power BI utilities
│   ├── file_utils.py       # File upload and processing
│   ├── powerbi_service.py  # Power BI API integration
│   ├── varima_detector.py  # VARIMA anomaly detection
│   ├── redis_client.py     # Redis cache management
│   └── requirements.txt    # Python dependencies
└── frontend/               # Next.js frontend application
    ├── app/                # Next.js app router pages
    ├── components/         # React components
    │   ├── ui/            # Reusable UI components
    │   └── unused/        # Archive of removed components
    ├── lib/               # Utility libraries
    └── hooks/             # Custom React hooks
```

## Installation & Setup

### Prerequisites
- Python 3.8+ with pip
- Node.js 18+ with npm/pnpm
- Redis server
- Database server (PostgreSQL/MySQL/SQL Server)

### Backend Setup
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Frontend Setup
```bash
cd frontend
npm install
# or
pnpm install
```

### Environment Configuration
Create `.env` file in backend directory:
```env
REDIS_URL=redis://localhost:6379
DATABASE_URL=your_database_connection_string
POWERBI_CLIENT_ID=your_powerbi_client_id
POWERBI_CLIENT_SECRET=your_powerbi_client_secret
POWERBI_TENANT_ID=your_powerbi_tenant_id
```

## Running the Application

### Start Backend Server
```bash
cd backend
.\venv\Scripts\activate
uvicorn main:app --host localhost --port 8000 --reload
```

### Start Frontend Development Server
```bash
cd frontend
npm run dev
# or
pnpm dev
```

Access the application at: `http://localhost:3000`

## Power BI Integration

### Current Implementation: Package-Based Approach

Due to the limitations of Power BI API access requiring **Premium accounts**, we have implemented a **downloadable package system** that provides:

#### What's Included in Power BI Packages:
- **Data Export**: `quality_statistics.csv` with comprehensive analysis results
- **Template File**: `dashboardDQ.pbit` (Power BI template for easy setup)
- **Pre-built Dashboard**: `dashboardDQ.pbix` (Ready-to-use dashboard file)
- **Setup Guide**: Step-by-step instructions for Power BI configuration

#### Package Features:
- **No Premium Account Required**: Works with Power BI Desktop (free)
- **Automated Data Export**: Quality metrics formatted for Power BI
- **Template-Based Setup**: Pre-configured visualizations and layouts
- **Cross-Platform**: Compatible with Power BI Desktop and Power BI Service
- **Offline Capability**: Works without internet connection

### Power BI API Integration (Premium Account Extension)

The codebase is **ready for Power BI API integration** when Premium accounts are available:

#### Available API Functionality:
```python
# powerbi_service.py contains full API implementation
- Authentication with Azure AD
- Workspace management
- Dataset creation and updates
- Report embedding
- Real-time data streaming
- Automated dashboard deployment
```

#### To Enable API Integration:
1. **Obtain Power BI Premium Account**
2. **Update Environment Variables**:
   ```env
   POWERBI_CLIENT_ID=your_premium_client_id
   POWERBI_CLIENT_SECRET=your_premium_client_secret
   POWERBI_TENANT_ID=your_tenant_id
   POWERBI_WORKSPACE_ID=your_workspace_id
   ```
3. **Enable API Routes**: Uncomment premium features in `routes.py`
4. **Frontend Integration**: Update frontend to use real-time embedding

#### Premium Features Ready for Activation:
- **Real-time Dashboard Embedding**: Direct Power BI dashboard integration
- **Automated Dataset Updates**: Live data streaming to Power BI
- **Workspace Management**: Programmatic dashboard deployment
- **Row-Level Security**: Advanced security configurations
- **Custom Visuals**: Enhanced visualization capabilities

## Data Quality Analysis

### Quality Metrics
- **Completeness**: Percentage of non-null values
- **Validity**: Data type consistency and format adherence
- **Consistency**: Pattern matching and business rule compliance
- **Uniqueness**: Duplicate detection and primary key validation
- **Accuracy**: Outlier detection and range validation

### Anomaly Detection
- **VARIMA Models**: Multivariate time series anomaly detection
- **Statistical Analysis**: Advanced outlier identification
- **Pattern Recognition**: Temporal and cross-variable anomaly detection
- **Threshold Configuration**: Customizable sensitivity settings

## API Endpoints

### Data Connections
- `POST /api/connect/database` - Connect to database
- `POST /api/connect/file` - Upload CSV file
- `GET /api/connections` - List active connections
- `DELETE /api/disconnect/{connection_id}` - Disconnect data source

### Analysis
- `POST /api/analysis/auto-quality-all-tables` - Analyze all tables
- `POST /api/analysis/quality-metrics` - Calculate specific metrics
- `POST /api/analysis/auto-varima-all-tables` - Run VARIMA detection
- `GET /api/analysis/cached-results/{connection_id}` - Get cached results

### Export & Power BI
- `POST /api/analysis/export-statistics` - Export quality statistics
- `POST /api/powerbi/open-online` - Create Power BI package
- `GET /api/download/powerbi-package/{connection_id}` - Download package

### Power BI Premium API (Ready for Activation)
- `POST /api/powerbi/authenticate` - Azure AD authentication
- `GET /api/powerbi/workspaces` - List workspaces
- `POST /api/powerbi/datasets/create` - Create dataset
- `POST /api/powerbi/embed-token` - Generate embed token

## Workflow

1. **Data Connection**: Connect to database or upload CSV file
2. **Quality Analysis**: Automated 5-dimensional quality assessment
3. **Anomaly Detection**: AI-powered VARIMA analysis for outliers
4. **Report Generation**: Comprehensive statistics and visualizations
5. **Power BI Integration**: Download package or use API (Premium)

## Development

### Modular Architecture
The backend follows a clean modular architecture:
- **Separation of Concerns**: Each module handles specific functionality
- **Easy Testing**: Independent module testing capabilities
- **Scalable Design**: Easy to extend and maintain
- **Clean Dependencies**: Clear module relationships

### Adding New Features
1. **Models**: Add new Pydantic models to `models.py`
2. **Routes**: Define API endpoints in `routes.py`
3. **Business Logic**: Implement functionality in appropriate modules
4. **Frontend**: Add components and integrate with API

### Testing
```bash
# Backend testing
cd backend
python -m pytest tests/

# Frontend testing
cd frontend
npm test
```

## Security Considerations

- **Environment Variables**: Sensitive data stored in `.env` files
- **Database Connections**: Encrypted connection strings
- **Redis Security**: Temporary data with expiration
- **File Upload Validation**: CSV format validation and size limits
- **CORS Configuration**: Restricted to allowed origins

## Performance Features

- **Redis Caching**: Analysis results cached for 1 hour
- **Streaming Responses**: Large file downloads via streaming
- **Connection Pooling**: Efficient database connection management
- **Async Processing**: Non-blocking API operations
- **Memory Optimization**: Chunked data processing for large datasets

## Configuration

### Database Support
- **PostgreSQL**: `postgresql://user:pass@host:port/db`
- **MySQL**: `mysql+pymysql://user:pass@host:port/db`
- **SQL Server**: `mssql+pyodbc://user:pass@host:port/db`

### Redis Configuration
- **Default**: `redis://localhost:6379`
- **Custom**: Configure via `REDIS_URL` environment variable

### File Upload Limits
- **Max File Size**: 50MB
- **Supported Formats**: CSV files only
- **Encoding**: UTF-8 with automatic detection

## Future Enhancements

### Planned Features
- **Machine Learning Models**: Advanced predictive analytics
- **Real-time Streaming**: Live data quality monitoring
- **Multi-tenant Support**: Organization-level data isolation
- **Advanced Visualizations**: Custom chart types and dashboards
- **API Rate Limiting**: Enhanced security and resource management

### Power BI Premium Integration
- **Real-time Embedding**: Direct dashboard integration
- **Automated Deployment**: Programmatic dashboard creation
- **Advanced Security**: Row-level security implementation
- **Custom Visuals**: Enhanced visualization library

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For questions, issues, or feature requests:
- **GitHub Issues**: Create an issue for bug reports or feature requests
- **Documentation**: Refer to module-specific documentation in `/docs`
- **Community**: Join our discussion forums for help and tips

## Related Resources

- **Power BI Documentation**: [Microsoft Power BI Docs](https://docs.microsoft.com/en-us/power-bi/)
- **FastAPI Documentation**: [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- **Next.js Documentation**: [Next.js Official Docs](https://nextjs.org/docs)
- **VARIMA Models**: [Time Series Analysis Documentation](https://www.statsmodels.org/)
