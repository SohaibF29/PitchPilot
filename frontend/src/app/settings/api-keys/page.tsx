'use client';

import React, { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { Card, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<any[]>([]);
  const [openaiKey, setOpenaiKey] = useState('');
  const [tavilyKey, setTavilyKey] = useState('');
  const [isSavingOpenai, setIsSavingOpenai] = useState(false);
  const [isSavingTavily, setIsSavingTavily] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const fetchKeys = async () => {
    try {
      const data = await api.getKeys();
      setKeys(data);
    } catch (err) {
      console.error('Failed to fetch keys hint:', err);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const handleSaveKey = async (provider: string, key: string, setLoader: (v: boolean) => void, setKeyVal: (v: string) => void) => {
    if (!key) return;
    setLoader(true);
    setSuccessMessage('');
    setErrorMessage('');
    try {
      await api.saveKey(provider, key);
      setSuccessMessage(`${provider.toUpperCase()} API Key saved securely!`);
      setTimeout(() => setSuccessMessage(''), 4000);
      setKeyVal('');
      fetchKeys();
    } catch (err: any) {
      setErrorMessage(`Failed to save key: ${err.message}`);
      setTimeout(() => setErrorMessage(''), 5000);
    } finally {
      setLoader(false);
    }
  };

  const handleDeleteKey = async (provider: string) => {
    if (!confirm(`Are you sure you want to remove your ${provider} API Key?`)) return;
    setSuccessMessage('');
    setErrorMessage('');
    try {
      await api.deleteKey(provider);
      setSuccessMessage(`Removed ${provider.toUpperCase()} credentials successfully.`);
      setTimeout(() => setSuccessMessage(''), 4000);
      fetchKeys();
    } catch (err: any) {
      setErrorMessage(`Failed to delete key: ${err.message}`);
      setTimeout(() => setErrorMessage(''), 5000);
    }
  };

  const getKeyHint = (provider: string) => {
    const key = keys.find((k) => k.provider === provider);
    return key ? key.key_hint : 'Not Configured';
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div>
        <span className="text-xxs font-bold text-[#8b5cf6] uppercase tracking-widest block">Configuration</span>
        <h2 className="text-2xl font-extrabold text-foreground mt-1">Credentials & Provider Keys</h2>
        <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
          Bring your own OpenAI or Tavily API Keys. Keys are encrypted symmetrically on the server before storage.
        </p>
      </div>

      {successMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 p-4 rounded-lg text-sm flex items-center gap-2">
          ✅ {successMessage}
        </div>
      )}
      {errorMessage && (
        <div className="bg-red-500/10 border border-red-500/30 text-red-700 dark:text-red-400 p-4 rounded-lg text-sm flex items-center gap-2">
          ❌ {errorMessage}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* OpenAI Key Configuration */}
        <Card className="space-y-6">
          <CardTitle>OpenAI API Key</CardTitle>
          <div className="text-xs text-slate-500 dark:text-slate-400">
            <strong>Current Key Status:</strong>{' '}
            <span
              className={`font-semibold ${
                getKeyHint('openai') !== 'Not Configured' ? 'text-[#10b981]' : 'text-red-500 dark:text-red-400'
              }`}
            >
              {getKeyHint('openai')}
            </span>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xxs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                Update Key
              </label>
              <input
                type="password"
                placeholder="sk-..."
                value={openaiKey}
                onChange={(e) => setOpenaiKey(e.target.value)}
                className="w-full bg-inputBg border border-inputBorder rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500 text-foreground transition-colors duration-200"
              />
            </div>
            <div className="flex gap-4">
              <Button
                variant="primary"
                onClick={() => handleSaveKey('openai', openaiKey, setIsSavingOpenai, setOpenaiKey)}
                disabled={isSavingOpenai}
                className="flex-1 text-xs py-2"
              >
                {isSavingOpenai ? 'Saving...' : 'Save Key'}
              </Button>
              {getKeyHint('openai') !== 'Not Configured' && (
                <Button variant="danger" onClick={() => handleDeleteKey('openai')} className="text-xs py-2">
                  Remove Key
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* Tavily Key Configuration */}
        <div className="space-y-6">
          <Card className="space-y-6">
          <div className="space-y-6">
            <CardTitle>Tavily Research API Key</CardTitle>
            <div className="text-xs text-slate-500 dark:text-slate-400">
              <strong>Current Key Status:</strong>{' '}
              <span
                className={`font-semibold ${
                  getKeyHint('tavily') !== 'Not Configured' ? 'text-[#10b981]' : 'text-red-500 dark:text-red-400'
                }`}
              >
                {getKeyHint('tavily')}
              </span>
            </div>

            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-xxs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider block">
                  Update Tavily Key
                </label>
                <input
                  type="password"
                  placeholder="tvly-..."
                  value={tavilyKey}
                  onChange={(e) => setTavilyKey(e.target.value)}
                  className="w-full bg-inputBg border border-inputBorder rounded-lg px-4 py-2.5 text-xs focus:outline-none focus:border-indigo-500 text-foreground transition-colors duration-200"
                />
              </div>
              <div className="flex gap-4">
                <Button
                  variant="primary"
                  onClick={() => handleSaveKey('tavily', tavilyKey, setIsSavingTavily, setTavilyKey)}
                  disabled={isSavingTavily}
                  className="flex-1 text-xs py-2"
                >
                  {isSavingTavily ? 'Saving...' : 'Save Key'}
                </Button>
                {getKeyHint('tavily') !== 'Not Configured' && (
                  <Button variant="danger" onClick={() => handleDeleteKey('tavily')} className="text-xs py-2">
                    Remove Key
                  </Button>
                )}
              </div>
            </div>
          </div>
          </Card>

          <div className="bg-indigo-950/20 border border-indigo-900/30 dark:bg-indigo-950/20 dark:border-indigo-900/30 p-4 rounded-lg text-xs text-indigo-700 dark:text-indigo-300 leading-relaxed transition-colors duration-300">
            💡 <strong>Pro-Tip:</strong> The Market Analyst boardroom member uses Tavily search to fetch real-time market sizes, demographic distributions, and competitors during analysis loops.
          </div>
        </div>
      </div>
    </div>
  );
}
