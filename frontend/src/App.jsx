import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import './styles/components.css';

const API_BASE = '/api';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('crag_token') || '');
  const [username, setUsername] = useState(localStorage.getItem('crag_username') || '');
  const [isRegistering, setIsRegistering] = useState(false);
  const [authForm, setAuthForm] = useState({ username: '', password: '' });
  const [authError, setAuthError] = useState('');

  const [conversations, setConversations] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [queryInput, setQueryInput] = useState('');

  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [pipelineLogs, setPipelineLogs] = useState([]);
  const [isQuerying, setIsQuerying] = useState(false);

  // Mobile: show sidebar or chat
  const [mobileView, setMobileView] = useState('sidebar'); // 'sidebar' | 'chat' | 'logs'

  // New session name input
  const [newSessionName, setNewSessionName] = useState('');
  const [showNewSession, setShowNewSession] = useState(false);

  const fileInputRef = useRef(null);
  const chatBottomRef = useRef(null);
  const tokenRef = useRef(token);

  useEffect(() => { tokenRef.current = token; }, [token]);

  const getHeaders = useCallback(() => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${tokenRef.current}`
  }), []);

  // Load data on login
  useEffect(() => {
    if (token) {
      fetchSessions();
      fetchDocuments();
    }
  }, [token]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchSessions = async () => {
    try {
      const res = await fetch(`${API_BASE}/chat/sessions`, { headers: getHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      setConversations(data);
      // Only auto-select if nothing is active
      if (data.length > 0) {
        setActiveSession(prev => prev ?? data[0]);
        await loadMessages(data[0]);
      }
    } catch (err) {
      console.error('fetchSessions error:', err);
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/documents`, { headers: getHeaders() });
      if (res.ok) setDocuments(await res.json());
    } catch (err) {
      console.error('fetchDocuments error:', err);
    }
  };

  const loadMessages = async (session) => {
    if (!session) return;
    try {
      const res = await fetch(`${API_BASE}/chat/sessions/${session.id}/messages`, { headers: getHeaders() });
      if (!res.ok) return;
      const data = await res.json();
      setMessages(data);
      const assistantMsgs = data.filter(m => m.role === 'assistant' && m.logs);
      if (assistantMsgs.length > 0) {
        setPipelineLogs(assistantMsgs[assistantMsgs.length - 1].logs);
      } else {
        setPipelineLogs([]);
      }
    } catch (err) {
      console.error('loadMessages error:', err);
    }
  };

  const selectSession = async (session) => {
    setActiveSession(session);
    setMessages([]);
    setPipelineLogs([]);
    setMobileView('chat');
    await loadMessages(session);
  };

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError('');
    const endpoint = isRegistering ? 'register' : 'login';
    try {
      const res = await fetch(`${API_BASE}/auth/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authForm)
      });
      const data = await res.json();
      if (!res.ok) { setAuthError(data.detail || 'Authentication failed'); return; }
      if (isRegistering) {
        setAuthError('');
        setIsRegistering(false);
        setAuthForm({ username: authForm.username, password: '' });
      } else {
        localStorage.setItem('crag_token', data.token);
        localStorage.setItem('crag_username', data.username);
        tokenRef.current = data.token;
        setToken(data.token);
        setUsername(data.username);
      }
    } catch {
      setAuthError('Cannot connect to server. Is the backend running?');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('crag_token');
    localStorage.removeItem('crag_username');
    setToken('');
    setUsername('');
    setConversations([]);
    setActiveSession(null);
    setMessages([]);
    setDocuments([]);
    setPipelineLogs([]);
    setMobileView('sidebar');
  };

  const handleCreateSession = async (e) => {
    e.preventDefault();
    const title = newSessionName.trim() || `Chat ${conversations.length + 1}`;
    setNewSessionName('');
    setShowNewSession(false);
    try {
      const res = await fetch(`${API_BASE}/chat/sessions`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ title })
      });
      if (res.ok) {
        const newSession = await res.json();
        setConversations(prev => [newSession, ...prev]);
        selectSession(newSession);
      }
    } catch (err) {
      console.error('createSession error:', err);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    e.target.value = '';
    setIsUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${tokenRef.current}` },
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        await fetchDocuments();
      } else {
        alert(data.detail || 'Upload failed');
      }
    } catch {
      alert('Upload failed: network error');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDocument = async (docId) => {
    if (!confirm('Delete this document from knowledge store?')) return;
    try {
      const res = await fetch(`${API_BASE}/documents/${docId}`, {
        method: 'DELETE', headers: getHeaders()
      });
      if (res.ok) setDocuments(prev => prev.filter(d => d.id !== docId));
    } catch (err) {
      console.error('deleteDocument error:', err);
    }
  };

  const handleQuerySubmit = async (e) => {
    e.preventDefault();
    if (!queryInput.trim() || !activeSession || isQuerying) return;
    const queryText = queryInput.trim();
    setQueryInput('');
    setIsQuerying(true);
    setMessages(prev => [...prev, { role: 'user', content: queryText }]);

    try {
      const res = await fetch(`${API_BASE}/chat/query`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ query: queryText, conversation_id: activeSession.id })
      });
      const data = await res.json();
      if (res.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.answer, logs: data.logs }]);
        setPipelineLogs(data.logs);
      } else {
        alert(data.detail || 'Query failed');
      }
    } catch {
      alert('Network error submitting query');
    } finally {
      setIsQuerying(false);
    }
  };

  // ─── AUTH SCREEN ──────────────────────────────────────────────────────────
  if (!token) {
    return (
      <div className="auth-overlay">
        <div className="auth-card glass">
          <div className="auth-logo">⚡</div>
          <h2>{isRegistering ? 'Create Account' : 'Welcome back'}</h2>
          <p>Corrective Retrieval-Augmented Generation</p>
          {authError && <div className="auth-error">{authError}</div>}
          <form onSubmit={handleAuth}>
            <div className="auth-input-group">
              <label>Username</label>
              <input
                id="auth-username"
                type="text"
                required
                autoFocus
                value={authForm.username}
                onChange={e => setAuthForm(p => ({ ...p, username: e.target.value }))}
              />
            </div>
            <div className="auth-input-group">
              <label>Password</label>
              <input
                id="auth-password"
                type="password"
                required
                value={authForm.password}
                onChange={e => setAuthForm(p => ({ ...p, password: e.target.value }))}
              />
            </div>
            <button id="auth-submit-btn" type="submit" className="auth-btn">
              {isRegistering ? 'Create Account' : 'Log In'}
            </button>
          </form>
          <div className="auth-toggle" onClick={() => { setIsRegistering(!isRegistering); setAuthError(''); }}>
            {isRegistering
              ? <>Already have an account? <span>Log In</span></>
              : <>No account yet? <span>Sign Up</span></>}
          </div>
        </div>
      </div>
    );
  }

  // ─── MAIN APP ─────────────────────────────────────────────────────────────
  return (
    <div className="app-container">

      {/* ── SIDEBAR ── */}
      <div className={`sidebar glass ${mobileView !== 'sidebar' ? 'sidebar-hidden' : ''}`}>
        <div className="sidebar-header">
          <span className="sidebar-logo">⚡</span>
          <h2>CRAG Platform</h2>
        </div>

        {/* New session button / inline form */}
        {showNewSession ? (
          <form onSubmit={handleCreateSession} className="new-session-form">
            <input
              autoFocus
              type="text"
              placeholder={`Chat ${conversations.length + 1}`}
              value={newSessionName}
              onChange={e => setNewSessionName(e.target.value)}
            />
            <div className="new-session-actions">
              <button type="submit" className="btn-primary-sm">Create</button>
              <button type="button" className="btn-ghost-sm" onClick={() => { setShowNewSession(false); setNewSessionName(''); }}>Cancel</button>
            </div>
          </form>
        ) : (
          <button id="new-chat-btn" onClick={() => setShowNewSession(true)} className="new-chat-btn">
            + New Chat
          </button>
        )}

        {/* Session list */}
        <div className="conversation-list">
          {conversations.length === 0 && (
            <div className="empty-hint">No chats yet. Create one above.</div>
          )}
          {conversations.map(c => (
            <div
              key={c.id}
              id={`session-${c.id}`}
              onClick={() => selectSession(c)}
              className={`conversation-item ${activeSession?.id === c.id ? 'active' : ''}`}
            >
              <span className="conv-icon">💬</span>
              <span className="conv-title">{c.title}</span>
            </div>
          ))}
        </div>

        {/* Knowledge Store */}
        <div className="doc-manager">
          <h3>Knowledge Store</h3>
          <div
            id="upload-zone"
            onClick={() => fileInputRef.current?.click()}
            className={`upload-zone ${isUploading ? 'uploading' : ''}`}
          >
            {isUploading ? '⏳ Indexing...' : '📁 Upload PDF / TXT / MD'}
          </div>
          <input
            type="file"
            accept=".pdf,.txt,.md"
            style={{ display: 'none' }}
            ref={fileInputRef}
            onChange={handleFileUpload}
          />

          {documents.length === 0 ? (
            <div className="empty-hint" style={{ marginTop: 10 }}>No documents yet.</div>
          ) : (
            <div className="file-list">
              {documents.map(d => (
                <div key={d.id} className="file-item">
                  <span title={d.filename}>📄 {d.filename}</span>
                  <button
                    id={`delete-doc-${d.id}`}
                    onClick={() => handleDeleteDocument(d.id)}
                    title="Delete document"
                  >&times;</button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* User footer */}
        <div className="sidebar-footer">
          <span className="sidebar-user">👤 {username}</span>
          <button id="logout-btn" onClick={handleLogout} className="logout-btn">Logout</button>
        </div>
      </div>

      {/* ── CHAT WINDOW ── */}
      <div className={`chat-window ${mobileView === 'sidebar' ? 'chat-hidden' : ''}`}>
        <div className="chat-header">
          {/* Back button (mobile + always visible) */}
          <button
            id="back-btn"
            className="back-btn"
            onClick={() => setMobileView('sidebar')}
            title="Back to sessions"
          >
            ← Back
          </button>
          <h1 id="chat-title">{activeSession?.title ?? 'Select a session'}</h1>
          <button
            className="logs-toggle-btn"
            onClick={() => setMobileView(v => v === 'logs' ? 'chat' : 'logs')}
            title="Toggle pipeline logs"
          >
            🧠 Logs
          </button>
        </div>

        <div className="chat-messages">
          {messages.length === 0 && !isQuerying && (
            <div className="chat-empty">
              <div className="chat-empty-icon">⚡</div>
              <p>Ask anything. If your documents don't have the answer, CRAG will search the web automatically.</p>
            </div>
          )}
          {messages.map((m, idx) => (
            <div key={idx} className={`message ${m.role}`}>
              <div className="message-bubble">
                {m.role === 'assistant' ? (
                  <ReactMarkdown
                    components={{
                      a: ({ node, ...props }) => (
                        <a {...props} target="_blank" rel="noopener noreferrer"
                          style={{ color: 'var(--secondary-color)', textDecoration: 'underline' }}
                        />
                      ),
                      h2: ({ node, ...props }) => (
                        <h2 {...props} style={{ fontSize: '1.05rem', marginBottom: '8px', marginTop: '4px', color: 'var(--text-primary)' }} />
                      ),
                      hr: ({ node, ...props }) => (
                        <hr {...props} style={{ border: 'none', borderTop: '1px solid var(--border-color)', margin: '10px 0' }} />
                      ),
                      li: ({ node, ...props }) => (
                        <li {...props} style={{ marginBottom: '4px', lineHeight: '1.55' }} />
                      ),
                      ul: ({ node, ...props }) => (
                        <ul {...props} style={{ paddingLeft: '20px', marginTop: '6px' }} />
                      ),
                      code: ({ node, ...props }) => (
                        <code {...props} style={{ background: 'rgba(99,102,241,0.12)', padding: '1px 6px', borderRadius: '4px', fontSize: '0.82rem', color: '#a5b4fc' }} />
                      ),
                      strong: ({ node, ...props }) => (
                        <strong {...props} style={{ color: 'var(--text-primary)', fontWeight: 600 }} />
                      ),
                    }}
                  >
                    {m.content}
                  </ReactMarkdown>
                ) : (
                  m.content
                )}
              </div>
            </div>
          ))}
          {isQuerying && (
            <div className="message assistant">
              <div className="message-bubble thinking">
                <span className="dot" /><span className="dot" /><span className="dot" />
                Running CRAG pipeline...
              </div>
            </div>
          )}
          <div ref={chatBottomRef} />
        </div>

        <div className="chat-input-container">
          <form onSubmit={handleQuerySubmit} className="chat-input-form">
            <input
              id="query-input"
              type="text"
              placeholder={activeSession ? 'Ask anything...' : 'Select or create a session first'}
              disabled={isQuerying || !activeSession}
              value={queryInput}
              onChange={e => setQueryInput(e.target.value)}
            />
            <button
              id="send-btn"
              type="submit"
              className="chat-send-btn"
              disabled={isQuerying || !activeSession || !queryInput.trim()}
            >
              ➤
            </button>
          </form>
        </div>
      </div>

      {/* ── PIPELINE LOGS ── */}
      <div className={`pipeline-pane glass ${mobileView === 'logs' ? 'logs-visible' : ''}`}>
        <div className="pipeline-header">
          <span>🧠 CRAG Pipeline</span>
          <button className="close-logs-btn" onClick={() => setMobileView('chat')}>✕</button>
        </div>
        <div className="pipeline-steps">
          {pipelineLogs.length === 0 ? (
            <div className="pipeline-empty">
              Submit a query to see the corrective agent execution logs here.
            </div>
          ) : (
            pipelineLogs.map((log, idx) => (
              <div key={idx} className={`step-card ${log.step.toLowerCase()}`}>
                <div className="step-title">{log.step.replace('_', ' ')}</div>
                <div className="step-body">{log.message}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
