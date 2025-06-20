/**
 * Configuration status component showing API readiness
 */

import React from 'react';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  Settings,
  Database,
  Cloud,
  Bot,
  Mail
} from 'lucide-react';
import { ConfigStatus } from '../utils/leadGenerator';

interface ConfigurationStatusProps {
  config: ConfigStatus | null;
  backendAvailable: boolean;
  onRefresh: () => void;
}

interface ConfigItem {
  name: string;
  key: keyof ConfigStatus;
  icon: React.ReactNode;
  description: string;
  required: boolean;
}

export const ConfigurationStatus: React.FC<ConfigurationStatusProps> = ({ 
  config, 
  backendAvailable, 
  onRefresh 
}) => {
  const configItems: ConfigItem[] = [
    {
      name: 'Google Places API',
      key: 'google_places_api',
      icon: <Cloud className="w-5 h-5" />,
      description: 'Required for business data scraping',
      required: true
    },
    {
      name: 'Database',
      key: 'database',
      icon: <Database className="w-5 h-5" />,
      description: 'SQLite database for data storage',
      required: true
    },
    {
      name: 'Perplexity AI',
      key: 'perplexity_api',
      icon: <Bot className="w-5 h-5" />,
      description: 'For company research and insights',
      required: false
    },
    {
      name: 'Anthropic Claude',
      key: 'anthropic_api',
      icon: <Bot className="w-5 h-5" />,
      description: 'For message personalization',
      required: false
    },
    {
      name: 'Instantly API',
      key: 'instantly_api',
      icon: <Mail className="w-5 h-5" />,
      description: 'For email campaign management',
      required: false
    }
  ];

  const getStatusIcon = (isConfigured: boolean, required: boolean) => {
    if (!backendAvailable) {
      return <XCircle className="w-5 h-5 text-gray-400" />;
    }
    
    if (isConfigured) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (required) {
      return <XCircle className="w-5 h-5 text-red-500" />;
    } else {
      return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusText = (isConfigured: boolean, required: boolean) => {
    if (!backendAvailable) {
      return 'Unavailable';
    }
    
    if (isConfigured) {
      return 'Configured';
    } else if (required) {
      return 'Required';
    } else {
      return 'Optional';
    }
  };

  const getStatusColor = (isConfigured: boolean, required: boolean) => {
    if (!backendAvailable) {
      return 'text-gray-500';
    }
    
    if (isConfigured) {
      return 'text-green-600';
    } else if (required) {
      return 'text-red-600';
    } else {
      return 'text-yellow-600';
    }
  };

  const getOverallStatus = () => {
    if (!backendAvailable) {
      return {
        status: 'Backend Unavailable',
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        description: 'Backend server is not running or accessible'
      };
    }

    if (!config) {
      return {
        status: 'Loading...',
        color: 'text-gray-600',
        bgColor: 'bg-gray-100',
        description: 'Checking configuration status'
      };
    }

    if (config.ready_for_pipeline) {
      return {
        status: 'Fully Ready',
        color: 'text-green-600',
        bgColor: 'bg-green-100',
        description: 'All systems configured for complete pipeline'
      };
    } else if (config.ready_for_scraping) {
      return {
        status: 'Basic Ready',
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-100',
        description: 'Ready for basic lead scraping (AI features disabled)'
      };
    } else {
      return {
        status: 'Not Ready',
        color: 'text-red-600',
        bgColor: 'bg-red-100',
        description: 'Missing required configuration'
      };
    }
  };

  const overallStatus = getOverallStatus();

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Settings className="w-6 h-6 text-gray-700 mr-3" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900">System Configuration</h2>
            <p className="text-sm text-gray-600">API status and system readiness</p>
          </div>
        </div>
        
        <button
          onClick={onRefresh}
          className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* Overall Status */}
      <div className={`${overallStatus.bgColor} ${overallStatus.color} rounded-lg p-4 mb-6`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold">{overallStatus.status}</h3>
            <p className="text-sm opacity-80">{overallStatus.description}</p>
          </div>
          {backendAvailable && config && (
            <div className="text-right text-sm">
              <div>Ready for campaigns: {config.ready_for_campaigns ? '✓' : '✗'}</div>
              <div>Ready for pipeline: {config.ready_for_pipeline ? '✓' : '✗'}</div>
              <div>Ready for scraping: {config.ready_for_scraping ? '✓' : '✗'}</div>
            </div>
          )}
        </div>
      </div>

      {/* Configuration Items */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {configItems.map((item) => {
          const isConfigured = config ? config[item.key] : false;
          
          return (
            <div
              key={item.key}
              className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow"
            >
              <div className="flex items-center mb-2">
                <div className="mr-3">
                  {item.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{item.name}</h4>
                  <div className="flex items-center">
                    {getStatusIcon(isConfigured, item.required)}
                    <span className={`ml-1 text-sm ${getStatusColor(isConfigured, item.required)}`}>
                      {getStatusText(isConfigured, item.required)}
                    </span>
                  </div>
                </div>
              </div>
              
              <p className="text-sm text-gray-600">{item.description}</p>
              
              {item.required && (
                <div className="mt-2">
                  <span className="inline-flex px-2 py-1 text-xs font-semibold bg-red-100 text-red-800 rounded-full">
                    Required
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Missing Configuration Warning */}
      {config && config.missing_configs.length > 0 && (
        <div className="mt-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-800">Missing Configuration</h4>
              <p className="text-sm text-yellow-700 mt-1">
                The following environment variables are not configured:
              </p>
              <ul className="list-disc list-inside text-sm text-yellow-700 mt-2">
                {config.missing_configs.map((configName) => (
                  <li key={configName}>{configName}</li>
                ))}
              </ul>
              <p className="text-sm text-yellow-700 mt-2">
                Add these to your .env file for full functionality.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Demo Mode Notice */}
      {!backendAvailable && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertTriangle className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-800">Demo Mode Active</h4>
              <p className="text-sm text-blue-700 mt-1">
                The backend server is not available. You can still explore the interface with demo data, 
                but no real lead generation will occur.
              </p>
              <p className="text-sm text-blue-700 mt-2">
                To enable full functionality, start the backend server and refresh this page.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfigurationStatus;
