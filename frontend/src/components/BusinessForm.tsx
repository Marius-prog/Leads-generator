/**
 * Business form component for lead generation parameters
 */

import React, { useState } from 'react';
import { Search, MapPin, Hash, Mail, Loader2 } from 'lucide-react';
import { LeadGenerationRequest } from '../utils/leadGenerator';

interface BusinessFormProps {
  onSubmit: (request: LeadGenerationRequest) => void;
  loading?: boolean;
  disabled?: boolean;
}

export const BusinessForm: React.FC<BusinessFormProps> = ({ 
  onSubmit, 
  loading = false, 
  disabled = false 
}) => {
  const [formData, setFormData] = useState({
    business_name: 'software companies',
    location: 'San Francisco, CA',
    leads_count: 25,
    campaign_name: '',
    from_email: '',
    include_research: true,
    include_personalization: true
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.business_name.trim()) {
      newErrors.business_name = 'Business type is required';
    }

    if (!formData.location.trim()) {
      newErrors.location = 'Location is required';
    }

    if (formData.leads_count < 1 || formData.leads_count > 100) {
      newErrors.leads_count = 'Number of leads must be between 1 and 100';
    }

    if (formData.from_email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.from_email)) {
      newErrors.from_email = 'Please enter a valid email address';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const request: LeadGenerationRequest = {
      business_name: formData.business_name.trim(),
      location: formData.location.trim(),
      leads_count: formData.leads_count,
      campaign_name: formData.campaign_name.trim() || undefined,
      from_email: formData.from_email.trim() || undefined,
      include_research: formData.include_research,
      include_personalization: formData.include_personalization
    };

    onSubmit(request);
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const predefinedBusinessTypes = [
    'restaurants',
    'dentists',
    'lawyers',
    'software companies',
    'marketing agencies',
    'real estate agents',
    'consulting firms',
    'retail stores',
    'fitness centers',
    'beauty salons'
  ];

  const predefinedLocations = [
    'San Francisco, CA',
    'New York, NY',
    'Los Angeles, CA',
    'Chicago, IL',
    'Houston, TX',
    'Phoenix, AZ',
    'Philadelphia, PA',
    'San Antonio, TX',
    'San Diego, CA',
    'Dallas, TX'
  ];

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Business Type */}
      <div>
        <label htmlFor="business_name" className="block text-sm font-medium text-gray-700 mb-2">
          Business Type
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            id="business_name"
            value={formData.business_name}
            onChange={(e) => handleInputChange('business_name', e.target.value)}
            className={`block w-full pl-10 pr-3 py-2 border ${errors.business_name ? 'border-red-300' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
            placeholder="e.g., restaurants, dentists, software companies"
            disabled={disabled}
            list="business-types"
          />
          <datalist id="business-types">
            {predefinedBusinessTypes.map(type => (
              <option key={type} value={type} />
            ))}
          </datalist>
        </div>
        {errors.business_name && (
          <p className="mt-1 text-sm text-red-600">{errors.business_name}</p>
        )}
      </div>

      {/* Location */}
      <div>
        <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-2">
          Location
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <MapPin className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            id="location"
            value={formData.location}
            onChange={(e) => handleInputChange('location', e.target.value)}
            className={`block w-full pl-10 pr-3 py-2 border ${errors.location ? 'border-red-300' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
            placeholder="e.g., San Francisco, CA"
            disabled={disabled}
            list="locations"
          />
          <datalist id="locations">
            {predefinedLocations.map(location => (
              <option key={location} value={location} />
            ))}
          </datalist>
        </div>
        {errors.location && (
          <p className="mt-1 text-sm text-red-600">{errors.location}</p>
        )}
      </div>

      {/* Number of Leads */}
      <div>
        <label htmlFor="leads_count" className="block text-sm font-medium text-gray-700 mb-2">
          Number of Leads
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Hash className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="number"
            id="leads_count"
            min="1"
            max="100"
            value={formData.leads_count}
            onChange={(e) => handleInputChange('leads_count', parseInt(e.target.value))}
            className={`block w-full pl-10 pr-3 py-2 border ${errors.leads_count ? 'border-red-300' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
            disabled={disabled}
          />
        </div>
        {errors.leads_count && (
          <p className="mt-1 text-sm text-red-600">{errors.leads_count}</p>
        )}
        <p className="mt-1 text-sm text-gray-500">Maximum 100 leads per search</p>
      </div>

      {/* Optional Fields */}
      <div className="border-t pt-6">
        <h3 className="text-sm font-medium text-gray-700 mb-4">Optional Settings</h3>
        
        {/* Campaign Name */}
        <div className="mb-4">
          <label htmlFor="campaign_name" className="block text-sm font-medium text-gray-700 mb-2">
            Campaign Name
          </label>
          <input
            type="text"
            id="campaign_name"
            value={formData.campaign_name}
            onChange={(e) => handleInputChange('campaign_name', e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            placeholder="My Lead Generation Campaign"
            disabled={disabled}
          />
        </div>

        {/* From Email */}
        <div className="mb-4">
          <label htmlFor="from_email" className="block text-sm font-medium text-gray-700 mb-2">
            From Email (for campaigns)
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="email"
              id="from_email"
              value={formData.from_email}
              onChange={(e) => handleInputChange('from_email', e.target.value)}
              className={`block w-full pl-10 pr-3 py-2 border ${errors.from_email ? 'border-red-300' : 'border-gray-300'} rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500`}
              placeholder="your@email.com"
              disabled={disabled}
            />
          </div>
          {errors.from_email && (
            <p className="mt-1 text-sm text-red-600">{errors.from_email}</p>
          )}
        </div>

        {/* Feature Toggles */}
        <div className="space-y-3">
          <div className="flex items-center">
            <input
              id="include_research"
              type="checkbox"
              checked={formData.include_research}
              onChange={(e) => handleInputChange('include_research', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={disabled}
            />
            <label htmlFor="include_research" className="ml-2 block text-sm text-gray-700">
              Include AI company research
            </label>
          </div>

          <div className="flex items-center">
            <input
              id="include_personalization"
              type="checkbox"
              checked={formData.include_personalization}
              onChange={(e) => handleInputChange('include_personalization', e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              disabled={disabled}
            />
            <label htmlFor="include_personalization" className="ml-2 block text-sm text-gray-700">
              Include message personalization
            </label>
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading || disabled}
        className="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Generating Leads...
          </>
        ) : (
          <>
            <Search className="w-4 h-4 mr-2" />
            Generate Leads
          </>
        )}
      </button>

      {disabled && (
        <div className="text-center text-sm text-gray-500">
          Backend not available - using demo mode
        </div>
      )}
    </form>
  );
};

export default BusinessForm;
