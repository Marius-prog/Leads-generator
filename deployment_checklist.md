
# Lead Generation System Deployment Checklist

## Pre-Deployment
- [ ] Add real API keys to .env file
- [ ] Verify Google Places API billing and quotas
- [ ] Test with small data set first
- [ ] Configure rate limiting for production
- [ ] Set up monitoring and logging

## API Configuration Required
- [ ] GOOGLE_PLACES_API_KEY (Required)
- [ ] PERPLEXITY_API_KEY (Required for research)
- [ ] ANTHROPIC_API_KEY (Required for personalization)
- [ ] INSTANTLY_API_KEY (Optional for campaigns)
- [ ] INSTANTLY_FROM_EMAIL (Optional for campaigns)

## Deployment Steps
1. Clone repository to production environment
2. Set up Python virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Configure environment variables in .env file
5. Test configuration: `python main.py setup-pipeline --check-apis`
6. Start system: `./start_fullstack.sh`

## Post-Deployment Testing
- [ ] Test health endpoints
- [ ] Run small lead generation test
- [ ] Verify database operations
- [ ] Test frontend interface
- [ ] Monitor system resources

## Production Considerations
- [ ] Set up proper logging
- [ ] Configure backup strategy for leads.db
- [ ] Implement monitoring and alerting
- [ ] Set up SSL certificates for production
- [ ] Configure firewall and security settings
