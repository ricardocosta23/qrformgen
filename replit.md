# QR Code Generator Service

## Overview

This is a Flask-based web service that generates QR codes with travel-themed backgrounds and integrates with Monday.com's API. The service creates QR codes for different categories (guides, clients, suppliers) with distinct color schemes and uploads them to Monday.com boards.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (July 15, 2025)

✓ Created complete Flask webhook application with 3 endpoints
✓ Implemented QR code generation with custom branded overlays  
✓ Added travel-themed background with landmark imagery
✓ Configured color-coded overlays (turquoise, purple, blue)
✓ Set up Monday.com API integration for file uploads
✓ Added health check endpoint and root API information endpoint
✓ Configured for Vercel deployment with vercel.json
✓ Updated webhook processing to query Monday.com for URLs from specific columns:
  - /qrguias queries column text_mkspdyty
  - /qrclientes queries column text_mksvzfm1  
  - /qrfornecedores queries column text_mksw9b2r
✓ Added Monday.com webhook challenge validation to all endpoints for proper webhook verification
✓ Fixed Monday.com file upload API format - now successfully uploads QR codes to board
✓ Completed testing - all endpoints working correctly with real Monday.com data
✓ Fixed background image loading - now uses actual travel landmark image
✓ Corrected semi-transparent overlay implementation - background now visible through overlay

## System Architecture

### Backend Framework
- **Flask**: Chosen for its simplicity and lightweight nature, perfect for a microservice that handles QR code generation
- **Python**: Selected for its excellent image processing libraries (PIL) and QR code generation capabilities

### Deployment Strategy
- **Vercel**: Configured for serverless deployment with Python runtime
- **Production-ready**: Uses environment variables for configuration and proper logging

## Key Components

### QR Code Generation
- **qrcode library**: Handles QR code creation with customizable parameters
- **PIL (Pillow)**: Manages image processing, background creation, and color overlays
- **Custom backgrounds**: Creates travel-themed backgrounds with gradient effects

### Monday.com Integration
- **API Integration**: Uses Monday.com's GraphQL API for board interactions
- **File Upload**: Handles QR code image uploads to specific board columns
- **Token-based Authentication**: Secured with API tokens

### Category System
Three distinct QR code categories:
- **qrguias** (Guides): Turquoise color scheme
- **qrclientes** (Clients): Purple color scheme  
- **qrfornecedores** (Suppliers): Blue color scheme

## Data Flow

1. **Webhook Reception**: Service receives webhook payload from Monday.com
2. **URL Extraction**: Extracts target URL from webhook data
3. **QR Code Generation**: Creates QR code with category-specific styling
4. **Background Processing**: Applies travel-themed background with color overlay
5. **File Upload**: Uploads generated QR code image back to Monday.com board

## External Dependencies

### Core Libraries
- **Flask**: Web framework
- **qrcode**: QR code generation
- **PIL (Pillow)**: Image processing
- **requests**: HTTP client for API calls

### Third-party Services
- **Monday.com API**: Project management platform integration
- **Vercel**: Serverless hosting platform

## Deployment Strategy

### Configuration
- **Environment Variables**: Sensitive data stored in environment variables
- **Vercel Deployment**: Serverless functions with automatic scaling
- **Production Logging**: Comprehensive logging for debugging and monitoring

### Security Considerations
- **API Token Management**: Monday.com tokens stored securely
- **Session Management**: Flask session security configured
- **CORS Handling**: Proper request handling for webhook endpoints

## Technical Decisions

### Image Processing Choice
- **PIL over OpenCV**: Chosen for lighter weight and sufficient image manipulation capabilities
- **In-memory Processing**: Images processed in memory using BytesIO for efficiency
- **Base64 Encoding**: Used for API file uploads to Monday.com

### Color System
- **RGBA with Transparency**: Semi-transparent overlays (50% opacity) for visual appeal
- **Category-specific Colors**: Distinct color schemes for easy visual identification
- **Gradient Backgrounds**: Enhanced visual appeal with sky-blue gradient effects

### API Integration
- **GraphQL**: Monday.com's preferred API format for efficient data queries
- **Webhook-driven**: Event-driven architecture for real-time QR code generation
- **Error Handling**: Comprehensive logging for troubleshooting API interactions