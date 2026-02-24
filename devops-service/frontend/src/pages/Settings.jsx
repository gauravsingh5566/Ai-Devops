import { useState } from 'react';
import { Settings as SettingsIcon, User, Key, Database } from 'lucide-react';
import toast from 'react-hot-toast';

const Settings = () => {
  const [userId, setUserId] = useState(localStorage.getItem('userId') || 'demo-user');

  const handleSaveUserId = () => {
    localStorage.setItem('userId', userId);
    toast.success('User ID saved');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-xl shadow-lg p-6">
        <h1 className="text-3xl font-bold text-white mb-2">Settings</h1>
        <p className="text-blue-100">Configure your DevOps platform</p>
      </div>

      {/* Settings Sections */}
      <div className="space-y-6">
        {/* User Settings */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <User className="text-blue-600" size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">User Settings</h2>
              <p className="text-sm text-gray-600">Configure your user preferences</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                User ID
              </label>
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Enter your user ID"
                />
                <button 
                  onClick={handleSaveUserId} 
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                >
                  Save
                </button>
              </div>
              <p className="mt-2 text-sm text-gray-500">
                This ID is used to identify your projects and builds
              </p>
            </div>
          </div>
        </div>

        {/* API Settings */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
              <Key className="text-purple-600" size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">API Configuration</h2>
              <p className="text-sm text-gray-600">API endpoint and authentication</p>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Base URL
              </label>
              <input
                type="text"
                value="http://localhost:8000"
                disabled
                className="w-full px-4 py-2 bg-gray-50 border border-gray-300 rounded-lg text-gray-600"
              />
              <p className="mt-2 text-sm text-gray-500">
                Configure in .env file: VITE_API_URL
              </p>
            </div>
          </div>
        </div>

        {/* System Info */}
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200 fade-in">
          <div className="flex items-center space-x-3 mb-6">
            <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
              <Database className="text-green-600" size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">System Information</h2>
              <p className="text-sm text-gray-600">Platform details and version</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <InfoCard label="Version" value="1.0.0" />
            <InfoCard label="Database" value="MongoDB" />
            <InfoCard label="Cache" value="Redis" />
            <InfoCard label="Queue" value="RabbitMQ" />
          </div>
        </div>
      </div>
    </div>
  );
};

const InfoCard = ({ label, value }) => (
  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
    <p className="text-sm text-gray-600">{label}</p>
    <p className="text-lg font-semibold text-gray-900 mt-1">{value}</p>
  </div>
);

export default Settings;