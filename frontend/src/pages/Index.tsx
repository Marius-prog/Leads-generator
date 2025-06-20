/**
 * Main dashboard page for lead generation system
 */

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Clock, Database, RefreshCw, Download } from 'lucide-react';
import { BusinessForm } from '../components/BusinessForm';
import { LeadsTable } from '../components/LeadsTable';
import { LeadsSummary } from '../components/LeadsSummary';
import { ConfigurationStatus } from '../components/ConfigurationStatus';
import { 
  leadGeneratorAPI, 
  LeadGenerationRequest, 
  TaskStatus, 
  ConfigStatus,
  demoLeads,
  formatTimestamp,
  getStatusColor,
  getStatusBadgeColor
} from '../utils/leadGenerator';

export interface Lead {
  id: number;
  campaign_id: string;
  place_id?: string;
  name: string;
  address: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  phone: string;
  email: string;
  website: string;
  category: string;
  rating?: number;
  reviews_count?: number;
  latitude?: number;
  longitude?: number;
  status: string;
  email_valid?: number | boolean;
  phone_valid?: number | boolean;
  company_valid?: number | boolean;
  linkedin_profile?: any;
  research_data?: any;
  personalized_message?: any;
  linkedin_enriched?: boolean;
  research_completed?: boolean;
  message_personalized?: boolean;
  created_at?: string;
  updated_at?: string;
}

const Index: React.FC = () => {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState<TaskStatus | null>(null);
  const [config, setConfig] = useState<ConfigStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [backendAvailable, setBackendAvailable] = useState(true);

  useEffect(() => {
    checkBackendAndConfig();
  }, []);

  useEffect(() => {
    let pollInterval: NodeJS.Timeout;
    
    if (currentTask && (currentTask.status === 'pending' || currentTask.status === 'running')) {
      pollInterval = setInterval(async () => {
        try {
          const updatedTask = await leadGeneratorAPI.getTaskStatus(currentTask.task_id);
          setCurrentTask(updatedTask);
          
          if (updatedTask.status === 'completed' && updatedTask.results) {
            // Fetch the actual leads data from the campaign
            try {
              const campaignId = updatedTask.results.campaign_id;
              if (campaignId) {
                const leadsResponse = await leadGeneratorAPI.getCampaignLeads(campaignId);
                if (leadsResponse.success && leadsResponse.data?.leads) {
                  setLeads(leadsResponse.data.leads);
                }
              }
            } catch (err) {
              console.error('Error fetching campaign leads:', err);
            }
            setLoading(false);
          } else if (updatedTask.status === 'failed') {
            setError(updatedTask.error_message || 'Pipeline failed');
            setLoading(false);
          }
        } catch (err) {
          console.error('Error polling task status:', err);
        }
      }, 2000);
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [currentTask]);

  const checkBackendAndConfig = async () => {
    try {
      await leadGeneratorAPI.healthCheck();
      const configStatus = await leadGeneratorAPI.checkConfig();
      setConfig(configStatus);
      setBackendAvailable(true);
      setError(null);
    } catch (err) {
      console.warn('Backend not available, using demo mode:', err);
      setBackendAvailable(false);
      setLeads(demoLeads);
      setConfig({
        google_places_api: false,
        perplexity_api: false,
        anthropic_api: false,
        instantly_api: false,
        database: false,
        missing_configs: ['All APIs (Demo Mode)'],
        ready_for_scraping: false,
        ready_for_pipeline: false,
        ready_for_campaigns: false
      });
    }
  };

  const handleGenerateLeads = async (request: LeadGenerationRequest) => {
    if (!backendAvailable) {
      // Demo mode - simulate lead generation
      setLoading(true);
      setError(null);
      
      setTimeout(() => {
        setLeads(demoLeads);
        setLoading(false);
        setCurrentTask({
          task_id: 'demo-task',
          status: 'completed',
          progress: 100,
          total_leads: demoLeads.length,
          processed_leads: demoLeads.length,
          results: { leads: demoLeads }
        });
      }, 2000);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setLeads([]);
      
      const taskResponse = await leadGeneratorAPI.generateLeads(request);
      
      const initialTask: TaskStatus = {
        task_id: taskResponse.task_id,
        status: 'pending',
        progress: 0,
        current_step: 'Starting pipeline'
      };
      
      setCurrentTask(initialTask);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start lead generation');
      setLoading(false);
    }
  };

  const handleRefreshConfig = async () => {
    await checkBackendAndConfig();
  };

  const handleClearResults = () => {
    setLeads([]);
    setCurrentTask(null);
    setError(null);
  };

  const handleExportResults = () => {
    if (leads.length === 0) return;
    
    const csv = [
      // CSV header
      ['Name', 'Address', 'Phone', 'Email', 'Website', 'Category', 'Rating', 'Reviews', 'Status', 'Email Valid', 'Phone Valid', 'Company Valid', 'LinkedIn Enriched', 'Research Completed', 'Message Personalized'].join(','),
      // CSV data
      ...leads.map(lead => [
        `"${lead.name || ''}"`,
        `"${lead.address || ''}"`,
        `"${lead.phone || ''}"`,
        `"${lead.email || ''}"`,
        `"${lead.website || ''}"`,
        `"${lead.category || ''}"`,
        lead.rating || '',
        lead.reviews_count || '',
        lead.status || '',
        lead.email_valid || false,
        lead.phone_valid || false,
        lead.company_valid || false,
        lead.linkedin_enriched || false,
        lead.research_completed || false,
        lead.message_personalized || false
      ].join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Lead Generation System</h1>
              <p className="mt-2 text-gray-600">
                Generate and validate business leads with AI-powered research and personalization
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              {!backendAvailable && (
                <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-3 py-2 rounded-lg text-sm">
                  Demo Mode - Backend Unavailable
                </div>
              )}
              
              <button
                onClick={handleRefreshConfig}
                className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
            </div>
          </div>
        </div>

        {/* Configuration Status */}
        <div className="mb-8">
          <ConfigurationStatus 
            config={config} 
            backendAvailable={backendAvailable}
            onRefresh={handleRefreshConfig}
          />
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        )}

        {/* Current Task Status */}
        {currentTask && (
          <div className="mb-6 bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Pipeline Status</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeColor(currentTask.status)}`}>
                {currentTask.status}
              </span>
            </div>
            
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span>Progress</span>
                <span>{currentTask.progress}%</span>
              </div>
              
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${currentTask.progress}%` }}
                />
              </div>
              
              {currentTask.current_step && (
                <p className="text-sm text-gray-600">
                  Current Step: {currentTask.current_step}
                </p>
              )}
              
              {currentTask.total_leads && (
                <p className="text-sm text-gray-600">
                  Leads Found: {currentTask.total_leads}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Lead Generation Form */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold mb-6">Generate New Leads</h2>
              <BusinessForm 
                onSubmit={handleGenerateLeads}
                loading={loading}
                disabled={!backendAvailable && loading}
              />
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2 space-y-6">
            {/* Summary Cards */}
            {leads.length > 0 && (
              <LeadsSummary leads={leads} />
            )}

            {/* Results Actions */}
            {leads.length > 0 && (
              <div className="bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">
                    Lead Results ({leads.length})
                  </h3>
                  
                  <div className="flex space-x-3">
                    <button
                      onClick={handleExportResults}
                      className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      Export CSV
                    </button>
                    
                    <button
                      onClick={handleClearResults}
                      className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                    >
                      Clear Results
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* Leads Table */}
            {leads.length > 0 ? (
              <LeadsTable leads={leads} />
            ) : !loading && !currentTask && (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No leads generated yet</h3>
                <p className="text-gray-600">
                  Use the form on the left to start generating leads for your business
                </p>
              </div>
            )}

            {/* Loading State */}
            {loading && !currentTask && (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4"></div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Generating Leads...</h3>
                <p className="text-gray-600">
                  Please wait while we search for businesses and validate the data
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
